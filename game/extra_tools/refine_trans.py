#!/usr/bin/env python3
"""
Refine transparent bounds of character sprites so all frames share the same crop box.

This script scans game/assets/sprites (or a provided directory), groups files by character
name using the naming convention:
  name_idle_1.png, name_idle_2.png, name_walk_1.png, name_walk_2.png

For each character group, it computes the union bounding box of non-transparent pixels
across all frames and then crops every frame to that common box, ensuring consistent
alignment in-game. By default, files are overwritten in place; optionally an output
directory can be specified.

Usage examples:
  python game/extra_tools/refine_trans.py
  python game/extra_tools/refine_trans.py --sprites-dir game/assets/sprites --out-dir game/assets/sprites
  python game/extra_tools/refine_trans.py --name cooper
  python game/extra_tools/refine_trans.py --dry-run
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from PIL import Image


SPRITE_SUFFIX_PATTERN = re.compile(r"_(idle|walk)_([0-9]+)\.png$", re.IGNORECASE)


def find_character_name(file_name: str) -> Optional[str]:
    """Extract the character base name from a sprite filename.

    Expected formats include:
      firstname_lastname_idle_1.png
      hero_walk_2.png
    Returns the base prefix (e.g., 'firstname_lastname' or 'hero') or None if not matched.
    """
    if not file_name.lower().endswith(".png"):
        return None
    match = SPRITE_SUFFIX_PATTERN.search(file_name)
    if not match:
        return None
    # remove the matched suffix from the end
    base = file_name[: match.start()]
    # strip any trailing underscores just in case
    return base.rstrip("_")


def compute_alpha_bbox(img: Image.Image) -> Optional[Tuple[int, int, int, int]]:
    """Compute the bounding box of non-transparent pixels.

    Returns a 4-tuple (left, upper, right, lower) or None if fully transparent.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[3]
    return alpha.getbbox()


def union_boxes(boxes: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    if not boxes:
        return None
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[2] for b in boxes)
    bottom = max(b[3] for b in boxes)
    return (left, top, right, bottom)


def refine_character_sprites(
    character: str,
    files: List[Path],
    out_dir: Path,
    dry_run: bool = False,
) -> None:
    """Refine all frames for one character by cropping to the union of alpha bboxes."""
    boxes = []
    opened: Dict[Path, Image.Image] = {}

    # First pass: compute union bbox
    for f in files:
        try:
            img = Image.open(f)
            opened[f] = img
            bbox = compute_alpha_bbox(img)
            if bbox:
                boxes.append(bbox)
        except Exception as e:
            print(f"Warning: failed to open {f}: {e}")

    union_bbox = union_boxes(boxes)
    if union_bbox is None:
        print(f"Skipping {character}: no opaque pixels found across frames")
        # cleanup opened images
        for img in opened.values():
            try:
                img.close()
            except Exception:
                pass
        return

    # Second pass: crop and save
    for f, img in opened.items():
        try:
            cropped = img.crop(union_bbox)
            rel_name = f.name  # preserve same filename
            out_path = out_dir / rel_name
            if dry_run:
                print(f"[dry-run] {f} -> {out_path} bbox={union_bbox} size={cropped.size}")
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                cropped.save(out_path)
                print(f"Saved {out_path} (bbox={union_bbox}, size={cropped.size})")
        except Exception as e:
            print(f"Warning: failed to process {f}: {e}")
        finally:
            try:
                img.close()
            except Exception:
                pass


def group_sprites_by_character(sprites_dir: Path) -> Dict[str, List[Path]]:
    groups: Dict[str, List[Path]] = {}
    for f in sprites_dir.glob("*.png"):
        base = find_character_name(f.name)
        if not base:
            continue
        groups.setdefault(base, []).append(f)
    return groups


def main() -> None:
    parser = argparse.ArgumentParser(description="Refine sprite transparent bounds to a shared crop box per character.")
    parser.add_argument("--sprites-dir", default="game/assets/sprites", help="Directory containing sprite PNGs")
    parser.add_argument("--out-dir", default=None, help="Output directory (defaults to overwriting in sprites-dir)")
    parser.add_argument("--name", default=None, help="Only process a specific character base name")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; print planned actions")
    args = parser.parse_args()

    sprites_dir = Path(args.sprites_dir)
    if not sprites_dir.exists():
        print(f"Sprites directory not found: {sprites_dir}")
        return

    out_dir = Path(args.out_dir) if args.out_dir else sprites_dir

    groups = group_sprites_by_character(sprites_dir)
    if not groups:
        print(f"No matching sprites found in {sprites_dir}")
        return

    if args.name:
        # process only requested character
        files = groups.get(args.name)
        if not files:
            print(f"No sprites found for character '{args.name}'")
            return
        refine_character_sprites(args.name, files, out_dir, dry_run=args.dry_run)
        return

    # process all characters
    for character, files in groups.items():
        refine_character_sprites(character, files, out_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()


