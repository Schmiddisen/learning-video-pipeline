"""Weights for the RWKV memory model in the player (rwkv.js).

Downloads the pretrained RWKV-7 spaced-repetition model of open-spaced-repetition/srs-benchmark
and converts the PyTorch checkpoint to a flat float32 file plus a JSON manifest, without torch:
a .pth file is a zip archive holding a pickle (tensor layout) and one raw buffer per storage.
The weights are cached in ~/.cache/lvp and never committed here.
"""

from __future__ import annotations

import hashlib
import json
import pickle
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


def ensure(dst: Path) -> bool:
    """Write rwkv_weights.wasm (raw float32) and rwkv_weights.json into dst; False if offline."""
    # raw float32, named .wasm: artifact hosting serves no .bin (fetched as an ArrayBuffer anyway)
    bin_path, man_path = dst / "rwkv_weights.wasm", dst / "rwkv_weights.json"
    cache_bin, cache_man = CACHE / "rwkv_weights.bin", CACHE / "rwkv_weights.json"
    if not (cache_bin.exists() and cache_man.exists()):
        CACHE.mkdir(parents=True, exist_ok=True)
        pth = CACHE / "RWKV_trained_on_101_4999.pth"
        if not pth.exists():
            try:
                print("[…] downloading the RWKV memory model (srs-benchmark, once, ~22 MB)")
                with urllib.request.urlopen(URL, timeout=120) as r:  # noqa: S310 - fixed https URL
                    data = r.read()
            except OSError as e:
                print(f"[!] RWKV download failed ({e}) – the player offers FSRS only")
                return False
            if hashlib.sha256(data).hexdigest() != SHA256:
                print("[!] RWKV download has an unexpected checksum – skipped")
                return False
            pth.write_bytes(data)
        manifest, blob = _read_pth(pth)
        cache_bin.write_bytes(blob)
        cache_man.write_text(json.dumps(manifest))
    dst.mkdir(parents=True, exist_ok=True)
    bin_path.write_bytes(cache_bin.read_bytes())
    man_path.write_text(cache_man.read_text())
    return True
