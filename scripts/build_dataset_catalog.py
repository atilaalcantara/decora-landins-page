#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import imagehash
import numpy as np
from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

CAPTION_EVENT_RULES = {
    "casamento": ["casamento", "noiva", "noivo", "wedding", "cerimonia", "cerimônia", "elopement"],
    "mini_wedding": ["miniwedding", "microwedding", "casamento intim"],
    "festa_15_anos": ["15 anos", "debutante", "quinze anos"],
    "evento_residencial": ["em casa", "quintal", "homewedding", "festaemcasa", "casamentoemcasa", "varanda"],
    "evento_corporativo": ["corporativo", "empresa", "evento empresarial"],
    "aniversario": ["aniversario", "aniversário"],
}

CAPTION_INSTALL_RULES = {
    "varal_de_luzes": ["varal", "luzinhas", "cordao de luz", "corda de luz"],
    "tunel_entrada": ["tunel", "túnel", "entrada", "cortina de led", "microled"],
    "lustre": ["lustre", "lustre paris"],
    "teto_iluminado": ["teto", "cabana", "pergolado", "gazebo", "tenda", "tipi", "teepee"],
    "letreiro": ["letreiro", "love iluminado"],
    "filamento": ["filamento", "retro"],
}

CAPTION_ENV_RULES = {
    "externo": ["ao ar livre", "campo", "fazenda", "chacara", "chácara", "jardim", "floresta", "sitio", "sítio"],
    "interno": ["salão", "salao", "hall", "pista"],
    "residencial": ["em casa", "quintal", "varanda", "jardim de casa", "piscina"],
    "entrada": ["entrada", "corredor", "hall"],
}


def normalize_text(text: str) -> str:
    text = text or ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w#@\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def keyword_in_text(text: str, keyword: str) -> bool:
    keyword = normalize_text(keyword)
    if not keyword:
        return False
    if " " in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def score_rules(text: str, rules: dict[str, list[str]], base: float = 0.55) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, words in rules.items():
        hits = sum(1 for w in words if keyword_in_text(text, w))
        if hits:
            out[key] = min(0.98, base + hits * 0.12)
    return out


def cap(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def laplacian_variance(gray: np.ndarray) -> float:
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    padded = np.pad(gray.astype(np.float32), 1, mode="edge")
    out = (
        kernel[0, 0] * padded[:-2, :-2]
        + kernel[0, 1] * padded[:-2, 1:-1]
        + kernel[0, 2] * padded[:-2, 2:]
        + kernel[1, 0] * padded[1:-1, :-2]
        + kernel[1, 1] * padded[1:-1, 1:-1]
        + kernel[1, 2] * padded[1:-1, 2:]
        + kernel[2, 0] * padded[2:, :-2]
        + kernel[2, 1] * padded[2:, 1:-1]
        + kernel[2, 2] * padded[2:, 2:]
    )
    return float(out.var())


def analyze_image(path: Path) -> dict[str, Any]:
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            w, h = im.size
            rgb = im.convert("RGB")
            small = rgb.copy()
            small.thumbnail((640, 640), Image.Resampling.LANCZOS)
            arr = np.asarray(small, dtype=np.float32)
            gray = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]

            mean_brightness = float(gray.mean())
            blur_var = laplacian_variance(gray)
            blur_score = cap((math.log10(blur_var + 1) - 0.9) / 2.3, 0.0, 1.0)
            exposure_score = cap(1.0 - abs(mean_brightness - 130.0) / 130.0, 0.0, 1.0)
            mp = (w * h) / 1_000_000
            res_score = cap(mp / 3.0, 0.0, 1.0)

            ratio = w / max(h, 1)
            if ratio > 1.12:
                orient = "landscape"
            elif ratio < 0.88:
                orient = "portrait"
            else:
                orient = "square"

            low_res_penalty = 0.0 if min(w, h) >= 600 else 0.18
            quality = cap(0.42 * res_score + 0.34 * blur_score + 0.2 * exposure_score + 0.04 * (1.0 if orient != "square" else 0.9) - low_res_penalty, 0.0, 1.0)

            return {
                "ok": True,
                "width": w,
                "height": h,
                "aspect_ratio": round(ratio, 4),
                "orientation": orient,
                "resolution_mp": round(mp, 3),
                "mean_brightness": round(mean_brightness, 2),
                "blur_variance": round(blur_var, 2),
                "blur_score": round(blur_score, 4),
                "quality_score": round(quality, 4),
                "phash": str(imagehash.phash(rgb, hash_size=8)),
            }
    except Exception as e:
        return {"ok": False, "error": e.__class__.__name__}


def discover_dataset(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    org_root = root / "organized_posts"

    if org_root.exists():
        for folder in sorted(org_root.iterdir()):
            if not folder.is_dir() or not folder.name.isdigit():
                continue
            image = next((x for x in folder.iterdir() if x.name.startswith("image") and x.suffix.lower() in IMAGE_EXTS), None)
            if not image:
                continue
            caption_path = folder / "caption.txt"
            caption = caption_path.read_text(encoding="utf-8", errors="ignore") if caption_path.exists() else ""
            records.append(
                {
                    "source": "organized_posts",
                    "post_key": folder.name,
                    "image_path": str(image),
                    "caption_path": str(caption_path) if caption_path.exists() else None,
                    "raw_caption": caption,
                }
            )

    # flat export
    txt_map: dict[str, Path] = {}
    for txt in root.glob("*.txt"):
        if re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_UTC$", txt.stem):
            txt_map[txt.stem] = txt

    for img in root.iterdir():
        if not img.is_file() or img.suffix.lower() not in IMAGE_EXTS:
            continue
        if not re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_UTC(?:_\d+)?$", img.stem):
            continue
        post_key = re.sub(r"_\d+$", "", img.stem)
        cap_path = txt_map.get(post_key)
        cap_text = cap_path.read_text(encoding="utf-8", errors="ignore") if cap_path and cap_path.exists() else ""
        records.append(
            {
                "source": "flat_export",
                "post_key": post_key,
                "image_path": str(img),
                "caption_path": str(cap_path) if cap_path else None,
                "raw_caption": cap_text,
            }
        )

    return records


@dataclass
class UnionFind:
    parent: list[int]
    rank: list[int]

    @classmethod
    def create(cls, n: int) -> "UnionFind":
        return cls(parent=list(range(n)), rank=[0] * n)

    def find(self, x: int) -> int:
        p = self.parent[x]
        while p != self.parent[p]:
            self.parent[p] = self.parent[self.parent[p]]
            p = self.parent[p]
        self.parent[x] = p
        return p

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def hardlink_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--dataset-dir", default="dataset")
    parser.add_argument("--near-dup-threshold", type=int, default=6)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    dataset_dir = (root / args.dataset_dir).resolve()

    # clean target tree
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
    for sub in ["raw", "processed", "images_clean", "duplicates", "low_quality"]:
        (dataset_dir / sub).mkdir(parents=True, exist_ok=True)

    records = discover_dataset(root)
    items: list[dict[str, Any]] = []

    for i, rec in enumerate(records, start=1):
        src = Path(rec["image_path"])
        visual = analyze_image(src)
        item = {
            "id": f"img-{i:05d}",
            **rec,
            "cleaned_caption": normalize_text(rec.get("raw_caption", "")),
            "caption_scores": {
                "event": score_rules(normalize_text(rec.get("raw_caption", "")), CAPTION_EVENT_RULES),
                "installation": score_rules(normalize_text(rec.get("raw_caption", "")), CAPTION_INSTALL_RULES),
                "environment": score_rules(normalize_text(rec.get("raw_caption", "")), CAPTION_ENV_RULES),
            },
            "sha256": sha256_file(src),
            **visual,
        }
        items.append(item)

    valid_idx = [i for i, x in enumerate(items) if x.get("ok")]
    uf = UnionFind.create(len(items))

    sha_groups: dict[str, list[int]] = defaultdict(list)
    for i, x in enumerate(items):
        sha_groups[x["sha256"]].append(i)
    for idxs in sha_groups.values():
        if len(idxs) > 1:
            for j in idxs[1:]:
                uf.union(idxs[0], j)

    phash_cache = {i: int(items[i]["phash"], 16) for i in valid_idx if items[i].get("phash")}
    for ai, i in enumerate(valid_idx):
        for j in valid_idx[ai + 1 :]:
            if i not in phash_cache or j not in phash_cache:
                continue
            if (phash_cache[i] ^ phash_cache[j]).bit_count() <= args.near_dup_threshold:
                if abs(items[i]["aspect_ratio"] - items[j]["aspect_ratio"]) <= 0.38:
                    uf.union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(items)):
        groups[uf.find(i)].append(i)

    # classify and place
    ai_jobs: list[dict[str, Any]] = []
    for gid, idxs in groups.items():
        idxs_sorted = sorted(
            idxs,
            key=lambda ix: (items[ix].get("quality_score", 0.0), items[ix].get("resolution_mp", 0.0)),
            reverse=True,
        )
        canonical = idxs_sorted[0]

        for rank, ix in enumerate(idxs_sorted, start=1):
            item = items[ix]
            item["duplicate_group"] = f"dup-{gid:05d}" if len(idxs_sorted) > 1 else None
            item["duplicate_flag"] = len(idxs_sorted) > 1 and ix != canonical
            item["is_canonical"] = ix == canonical
            item["duplicate_rank"] = rank

            low_quality = (
                (not item.get("ok"))
                or item.get("quality_score", 0) < 0.33
                or min(item.get("width", 0), item.get("height", 0)) < 480
            )
            item["low_quality_flag"] = bool(low_quality)

            src = Path(item["image_path"])
            short = f"{item['id']}-{src.name}"

            if item["duplicate_flag"]:
                dst = dataset_dir / "duplicates" / short
                item["dataset_bucket"] = "duplicates"
            elif item["low_quality_flag"]:
                dst = dataset_dir / "low_quality" / short
                item["dataset_bucket"] = "low_quality"
            else:
                dst = dataset_dir / "images_clean" / short
                item["dataset_bucket"] = "images_clean"
                ai_jobs.append({"id": item["id"], "image_path": str(dst), "cleaned_caption": item["cleaned_caption"]})

            if src.exists():
                hardlink_or_copy(src, dst)
            item["dataset_image_path"] = str(dst.relative_to(root))

    # raw pointers
    raw_manifest = {
        "organized_posts_path": str((root / "organized_posts").resolve()),
        "flat_export_root": str(root),
        "notes": "raw source kept in-place; processed dataset references below",
    }
    (dataset_dir / "raw" / "manifest.json").write_text(json.dumps(raw_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    (dataset_dir / "processed" / "ai_jobs.json").write_text(json.dumps(ai_jobs, indent=2, ensure_ascii=False), encoding="utf-8")

    base_catalog = {
        "summary": {
            "total_items": len(items),
            "clean_items": sum(1 for x in items if x["dataset_bucket"] == "images_clean"),
            "duplicate_items": sum(1 for x in items if x["dataset_bucket"] == "duplicates"),
            "low_quality_items": sum(1 for x in items if x["dataset_bucket"] == "low_quality"),
            "ai_jobs": len(ai_jobs),
        },
        "items": items,
    }

    (dataset_dir / "catalog_base.json").write_text(json.dumps(base_catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    (dataset_dir / "catalog.json").write_text(json.dumps(base_catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(base_catalog["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
