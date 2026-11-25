"""Transcribe recordings (lectures, talks, podcasts) locally with faster-whisper.

Videos never leave the machine: audio is decoded in-process (PyAV), the model runs
locally, and only the resulting text files are written to ``material/transcripts/``.

Usage (from the repo root):
    uv run lvp-transcribe                      # everything in material/recordings/
    uv run lvp-transcribe talk.mp4 more/       # specific file(s) or folder(s)
    uv run lvp-transcribe --model medium       # smaller/faster model
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".mp3", ".wav", ".m4a", ".flac"}


# Optional domain vocabulary nudges Whisper towards correct spelling of technical terms:
# put the terms of your course into material/vocabulary.txt (one line, comma-separated).
def _vocabulary() -> str | None:
    from lvp.project import MATERIAL

    f = MATERIAL / "vocabulary.txt"
    return f.read_text(encoding="utf-8").strip() if f.exists() else None


@dataclass
class Word:
    start: float
    end: float
    word: str
    probability: float


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)


def _register_windows_cuda_dlls() -> None:
    """Make pip-installed NVIDIA DLLs (``--extra gpu``) visible to CTranslate2 on Windows."""
    if os.name != "nt":
        return
    for base in map(Path, sys.path):
        nvidia = base / "nvidia"
        if not nvidia.is_dir():
            continue
        for bin_dir in nvidia.glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"


def _fetch_model(name: str) -> str:
    """Download the model with a visible progress bar (faster-whisper hides it)."""
    from faster_whisper.utils import _MODELS

    repo = name if "/" in name else _MODELS.get(name)
    if repo is None or Path(name).is_dir():
        return name
    from huggingface_hub import snapshot_download

    print(f"[i] Loading model '{name}' (first run downloads ~3 GB, cached afterwards) ...")
    return snapshot_download(
        repo,
        allow_patterns=[
            "config.json",
            "preprocessor_config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.*",
        ],
    )


def _load_model(name: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel

    label, name = name, _fetch_model(name)

    if device in ("auto", "cuda"):
        _register_windows_cuda_dlls()
        try:
            import ctranslate2

            if ctranslate2.get_cuda_device_count() > 0:
                ct = "float16" if compute_type == "auto" else compute_type
                model = WhisperModel(name, device="cuda", compute_type=ct)
                print(f"[i] Model '{label}' running on GPU (CUDA, {ct}).")
                return model
            if device == "cuda":
                raise RuntimeError("No CUDA GPU found.")
        except Exception as exc:  # noqa: BLE001 - fall back to CPU on any CUDA problem
            if device == "cuda":
                raise
            print(f"[!] GPU not usable ({exc}). Falling back to CPU.")

    ct = "int8" if compute_type == "auto" else compute_type
    print(f"[i] Model '{label}' running on CPU ({ct}). This is much slower.")
    return WhisperModel(name, device="cpu", compute_type=ct)


def _collect(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in VIDEO_EXTS))
        elif p.is_file():
            files.append(p)
        else:
            print(f"[!] Not found: {p}")
    return files


def _ts(seconds: float, sep: str = ",") -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{sep}{ms:03}"


def _write_atomic(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    tmp.replace(path)


def _write_outputs(out_dir: Path, stem: str, source: Path, info, segments: list[Segment]) -> None:
    meta = {
        "source_file": source.name,  # name only - no local paths in the repo
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
        "duration_seconds": round(info.duration, 2),
    }
    payload = {"meta": meta, "segments": [asdict(s) for s in segments]}
    _write_atomic(out_dir / f"{stem}.json", json.dumps(payload, ensure_ascii=False, indent=1))

    srt = "\n".join(
        f"{i}\n{_ts(s.start)} --> {_ts(s.end)}\n{s.text}\n" for i, s in enumerate(segments, 1)
    )
    _write_atomic(out_dir / f"{stem}.srt", srt)

    header = f"# Transkript: {stem}\n\nDauer: {_ts(info.duration, '.')[:8]}\n\n"
    body = "\n".join(f"`[{_ts(s.start, '.')[:8]}]` {s.text}  " for s in segments)
    _write_atomic(out_dir / f"{stem}.md", header + body + "\n")


def transcribe_file(model, src: Path, out_dir: Path, language: str, beam_size: int) -> None:
    t0 = time.monotonic()
    seg_iter, info = model.transcribe(
        str(src),
        language=language,
        beam_size=beam_size,
        word_timestamps=True,
        vad_filter=True,
        initial_prompt=_vocabulary(),
        condition_on_previous_text=False,  # avoids repetition loops on long lectures
    )
    print(f"    duration {_ts(info.duration, '.')[:8]}, transcribing ...", flush=True)
    segments: list[Segment] = []
    for seg in seg_iter:
        words = [
            Word(round(w.start, 3), round(w.end, 3), w.word, round(w.probability, 3))
            for w in (seg.words or [])
        ]
        segments.append(Segment(round(seg.start, 3), round(seg.end, 3), seg.text.strip(), words))
        pct = min(100.0, seg.end / max(info.duration, 1) * 100)
        print(f"\r    {pct:5.1f} %  [{_ts(seg.end, '.')[:8]}]", end="", flush=True)
    print()
    _write_outputs(out_dir, src.stem, src, info, segments)
    print(f"    done in {(time.monotonic() - t0) / 60:.1f} min, {len(segments)} segments.")


def main(argv: list[str] | None = None) -> int:
    # Windows without Developer Mode can't symlink; the HF cache still works, just bigger.
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # umlauts in the Windows console

    parser = argparse.ArgumentParser(description="Transcribe lecture videos locally.")
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        default=[Path("material/recordings")],
        help="audio/video files or folders (default: material/recordings)",
    )
    parser.add_argument("--out", type=Path, default=Path("material/transcripts"))
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model: large-v3 (best quality), turbo, medium, small",
    )
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument(
        "--compute-type",
        default="auto",
        help="e.g. float16, int8_float16, int8 (default: automatic)",
    )
    parser.add_argument("--language", default=None, help="e.g. en, de (default: autodetect)")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--overwrite", action="store_true", help="re-create existing transcripts")
    args = parser.parse_args(argv)

    files = _collect(args.inputs)
    if not files:
        print("[!] Nothing found. Put recordings in material/recordings/ or pass a path.")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    todo = [f for f in files if args.overwrite or not (args.out / f"{f.stem}.json").exists()]
    for f in sorted(set(files) - set(todo)):
        print(f"[=] Skipped (already transcribed): {f.name}")
    if not todo:
        return 0

    model = _load_model(args.model, args.device, args.compute_type)
    for i, src in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {src.name}")
        transcribe_file(model, src, args.out, args.language, args.beam_size)

    print(f"\n[✓] Transcripts written to: {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
