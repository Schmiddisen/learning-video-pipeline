"""Weights for the RWKV memory model in the player (rwkv.js).

Two models, both converted to a flat float32 file plus a JSON manifest, without torch:

- ``sm118`` (default): the "Small" two-head model of the RWKV Anki fork (JSchoreels/anki,
  qt/aqt/rwkv_inference/sm118): d_model 64, ~332k parameters, a mixture of three power-law
  forgetting curves. Its export is a simple tensor container (``ARWKVWEIGHTS1``).
- ``srs-benchmark``: the pretrained RWKV-7 checkpoint of open-spaced-repetition/srs-benchmark
  (a .pth zip: a pickle with the tensor layout and one raw buffer per storage).

Weights notice (JSchoreels/anki, WEIGHTS-NOTICE.md): the trained weights are not under an open
license; they follow the terms of the anki-revlogs-10k data they were trained on, which allow
personal use and individual research. Shipping them in an application needs Anki's permission.
So they are downloaded on the learner's machine for their own player and never committed here.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import struct
import urllib.request
import zipfile
from pathlib import Path

COMMIT = "57c0b0700c8a63cc7b68ffb9c8270271db8fd021"
URL = (
    "https://raw.githubusercontent.com/open-spaced-repetition/srs-benchmark/"
    f"{COMMIT}/pretrain/RWKV_trained_on_101_4999.pth"
)
SHA256 = "82d60a4de2e26b4064b86359874e458d1546c0e9651c5dbdf9b8f449a9b97114"
CACHE = Path.home() / ".cache" / "lvp"

FORK_COMMIT = "36c4f39d7a9880063656981b7d1f35dd23a38007"
FORK_URL = f"https://raw.githubusercontent.com/JSchoreels/anki/{FORK_COMMIT}/qt/aqt/rwkv_inference/"
MODELS = {  # name: {file: sha256} (hashes as published in the fork's manifest.json)
    "sm118": {
        "weights.f32.bin": "379168c80e8d546ebac892adda49e9a012b71c92b44cf8c9f94d4202f2530c3c",
        "architecture.json": "9bd41f1189dc0113277d371223ce805612aaec07101804160fe86312eed15de3",
    },
}
DEFAULT_MODEL = "sm118"


class _Storage:
    def __init__(self, key: str, dtype: str):
        self.key, self.dtype = key, dtype


class _Tensor:
    def __init__(self, storage, offset, shape, stride):
        self.storage, self.offset = storage, offset
        self.shape, self.stride = tuple(shape), tuple(stride)


def _rebuild(storage, offset, shape, stride, *_):
    return _Tensor(storage, offset, shape, stride)


class _Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name in ("_rebuild_tensor_v2", "_rebuild_tensor"):
            return _rebuild
        if module == "collections" and name == "OrderedDict":
            import collections

            return collections.OrderedDict
        if module == "torch" and name.endswith("Storage"):
            return name
        raise pickle.UnpicklingError(f"unexpected object in checkpoint: {module}.{name}")

    def persistent_load(self, pid):
        # ('storage', storage_type, key, location, numel)
        return _Storage(str(pid[2]), str(pid[1]))


def _read_pth(path: Path) -> tuple[list[dict], bytes]:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        root = names[0].split("/")[0]
        state = _Unpickler(z.open(f"{root}/data.pkl")).load()
        manifest, chunks, offset = [], [], 0
        for name, t in state.items():
            if not isinstance(t, _Tensor):
                continue
            if t.storage.dtype not in ("FloatStorage", "torch.FloatStorage"):
                raise ValueError(f"{name}: expected float32, got {t.storage.dtype}")
            raw = z.read(f"{root}/data/{t.storage.key}")
            n = 1
            for d in t.shape:
                n *= d
            # contiguous row-major check
            want, s = [], 1
            for d in reversed(t.shape):
                want.append(s)
                s *= d
            if n > 1 and tuple(reversed(want)) != t.stride:
                raise ValueError(f"{name}: non-contiguous tensor")
            chunks.append(raw[t.offset * 4 : (t.offset + n) * 4])
            manifest.append({"name": name, "shape": list(t.shape), "offset": offset})
            offset += n
    return manifest, b"".join(chunks)


def _download(url: str, sha256: str, what: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=120) as r:  # noqa: S310 - fixed https URL
            data = r.read()
    except OSError as e:
        print(f"[!] RWKV download failed ({e}) – the player offers FSRS only")
        return None
    if hashlib.sha256(data).hexdigest() != sha256:
        print(f"[!] RWKV {what} has an unexpected checksum – skipped")
        return None
    return data


def _read_fork_export(data: bytes) -> tuple[list[dict], bytes]:
    """The fork's tensor container: magic, count, then name, rank, shape and float32 values."""
    if not data.startswith(b"ARWKVWEIGHTS1"):
        raise ValueError("not an ARWKVWEIGHTS1 export")
    pos, manifest, chunks, offset = 13, [], [], 0

    def take(fmt: str):
        nonlocal pos
        size = struct.calcsize(fmt)
        value = struct.unpack_from(fmt, data, pos)
        pos += size
        return value

    (count,) = take("<I")
    for _ in range(count):
        (name_len,) = take("<H")
        name = data[pos : pos + name_len].decode()
        pos += name_len
        (rank,) = take("<B")
        shape = list(take(f"<{rank}I")) if rank else []
        n = 1
        for d in shape:
            n *= d
        chunks.append(data[pos : pos + 4 * n])
        pos += 4 * n
        manifest.append({"name": name, "shape": shape, "offset": offset})
        offset += n
    if pos != len(data):
        raise ValueError("trailing bytes in weights export")
    return manifest, b"".join(chunks)


def _build(model: str) -> tuple[dict | list, bytes] | None:
    if model == "srs-benchmark":
        pth = CACHE / "RWKV_trained_on_101_4999.pth"
        if not pth.exists():
            print("[…] downloading the RWKV memory model (srs-benchmark, once, ~22 MB)")
            data = _download(URL, SHA256, "checkpoint")
            if data is None:
                return None
            pth.write_bytes(data)
        return _read_pth(pth)
    files = MODELS[model]
    print(f"[…] downloading the RWKV memory model ({model} of the RWKV Anki fork, once, ~1.4 MB)")
    got = {f: _download(FORK_URL + f"{model}/{f}", h, f) for f, h in files.items()}
    if any(v is None for v in got.values()):
        return None
    tensors, blob = _read_fork_export(got["weights.f32.bin"])
    arch = json.loads(got["architecture.json"])
    manifest = {
        "format": 2,
        "model": model,
        "tensors": tensors,
        "steps": arch["layer_steps"],
        "zero_features": arch.get("zero_features", []),
    }
    return manifest, blob


def ensure(dst: Path, model: str = DEFAULT_MODEL) -> bool:
    """Write rwkv_weights.wasm (raw float32) and rwkv_weights.json into dst; False if offline."""
    # raw float32, named .wasm: artifact hosting serves no .bin (fetched as an ArrayBuffer anyway)
    bin_path, man_path = dst / "rwkv_weights.wasm", dst / "rwkv_weights.json"
    cache_bin, cache_man = CACHE / f"rwkv-{model}.bin", CACHE / f"rwkv-{model}.json"
    if not (cache_bin.exists() and cache_man.exists()):
        CACHE.mkdir(parents=True, exist_ok=True)
        built = _build(model)
        if built is None:
            return False
        manifest, blob = built
        cache_bin.write_bytes(blob)
        cache_man.write_text(json.dumps(manifest))
    dst.mkdir(parents=True, exist_ok=True)
    bin_path.write_bytes(cache_bin.read_bytes())
    man_path.write_text(cache_man.read_text())
    return True
