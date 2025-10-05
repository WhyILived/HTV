#!/usr/bin/env python3
"""
Dialogue generation pipeline using ElevenLabs TTS.

Features:
- Creates/selects an ElevenLabs voice profile per character based on type/mood.
- Reads dialogues from storyline JSON (root `storyline.json` or `game/storyline.json`).
- Synthesizes lines to `game/assets/dialogues/<character>/<scene_or_cutscene>/line_XX.mp3`.

Environment:
- Requires ELEVENLABS_API_KEY in environment (loaded via dotenv).

Notes:
- If a specific voice is unavailable or creation fails, falls back to a built-in voice per type.
- Safe, idempotent directory handling; skips regeneration if target file exists unless force=True.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv

# ElevenLabs SDK imports (lazy error message if missing)
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
except Exception:  # pragma: no cover - handled at runtime
    ElevenLabs = None  # type: ignore
    VoiceSettings = None  # type: ignore


load_dotenv(override=True)


def _find_storyline_file() -> Path:
    """Find storyline JSON (prefer project-root `storyline.json`, fallback to `game/storyline.json`)."""
    root = Path(__file__).resolve().parents[2]
    candidates = [root / "storyline.json", root / "game" / "storyline.json"]
    for c in candidates:
        if c.exists():
            return c
    # Default to root path even if missing; caller will handle error
    return candidates[0]


def _load_storyline(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_char_type(char_type: str) -> str:
    t = (char_type or "").strip().lower()
    if t in ("male", "female", "robot"):
        return t
    # Heuristic: treat non-human types as robot
    if "robot" in t or "ai" in t or "android" in t:
        return "robot"
    # default male for missing/unknown
    return "male"


def _collect_characters(story: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return list of character dicts with name and type; includes main_character."""
    characters: List[Dict[str, str]] = []

    # main_character may be nested under {"main_character": {...}}
    mc = story.get("main_character")
    if isinstance(mc, dict):
        main_obj = mc.get("main_character") if "main_character" in mc else mc
        if isinstance(main_obj, dict):
            characters.append({
                "name": str(main_obj.get("name", "MainCharacter")),
                "type": _normalize_char_type(str(main_obj.get("type", "male"))),
                "mood": str(main_obj.get("mood", "")),
            })

    # characters may be under {"characters": [...]}
    cs = story.get("characters")
    if isinstance(cs, dict) and "characters" in cs:
        cs = cs.get("characters")
    if isinstance(cs, list):
        for c in cs:
            if not isinstance(c, dict):
                continue
            characters.append({
                "name": str(c.get("name", "Character")),
                "type": _normalize_char_type(str(c.get("type", "male"))),
                "mood": str(c.get("mood", "")),
            })
    return characters


def _collect_dialogue_lines(story: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Extract dialogue lines.
    Returns a list of tuples (speaker_name, text, grouping_key).
    grouping_key designates scene/cutscene context for folder naming.
    """
    lines: List[Tuple[str, str, str]] = []

    # From characters dialogue arrays (if present)
    cs = story.get("characters")
    if isinstance(cs, dict) and "characters" in cs:
        cs = cs.get("characters")
    if isinstance(cs, list):
        for c in cs:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", "Character"))
            dlist = c.get("dialogue", [])
            if isinstance(dlist, list):
                for i, line in enumerate(dlist):
                    if not isinstance(line, str):
                        continue
                    lines.append((name, line, f"character_{name}"))

    # From cutscenes dialogue blocks
    cuts = story.get("cutscenes")
    if isinstance(cuts, dict) and "cutscenes" in cuts:
        cuts = cuts.get("cutscenes")
    if isinstance(cuts, list):
        for c in cuts:
            if not isinstance(c, dict):
                continue
            cid = c.get("id", "unknown")
            dlist = c.get("dialogue", [])
            if isinstance(dlist, list):
                for i, d in enumerate(dlist):
                    if not isinstance(d, dict):
                        continue
                    speaker = str(d.get("speaker", "Narrator"))
                    text = str(d.get("line", ""))
                    if text:
                        lines.append((speaker, text, f"cutscene_{cid}"))

    return lines


def _get_elevenlabs_client() -> ElevenLabs:
    if ElevenLabs is None:
        raise RuntimeError("elevenlabs package not installed. Please run: pip install elevenlabs")
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set. Add it to your .env or environment.")
    return ElevenLabs(api_key=api_key)


def _pick_fallback_voice_id(char_type: str) -> str:
    """Static fallback voices by type using public premade voices."""
    mapping = {
        "male": "21m00Tcm4TlvDq8ikWAM",   # Adam
        "female": "EXAVITQu4vr4xnSDxMaL", # Bella
        "robot": "AZnzlk1XvdvUeBnXmlld",  # Arnold
    }
    return mapping.get(char_type, mapping["male"])


def _voice_settings_for(type_: str, mood: str) -> VoiceSettings:
    # Tweak clarity/stability based on mood/type
    stability = 0.4
    similarity_boost = 0.7
    style = 0.0
    speaker_boost = True

    t = type_.lower()
    m = mood.lower()
    if t == "robot":
        stability = 0.8
        similarity_boost = 0.3
    if m in ("stoic", "grumpy"):
        stability = max(stability, 0.7)
    if m in ("witty", "optimistic"):
        style = 0.3

    return VoiceSettings(
        stability=stability,
        similarity_boost=similarity_boost,
        style=style,
        use_speaker_boost=speaker_boost,
    )


def _get_or_create_voice_id(client: ElevenLabs, name: str, type_: str, mood: str) -> str:
    """
    Try to find an existing voice by name; otherwise fall back to a premade per type.
    Note: Programmatic custom-voice creation requires audio samples; we use premade voices selected by type/mood.
    """
    try:
        voices = client.voices.get_all().voices  # type: ignore[attr-defined]
        for v in voices:
            if getattr(v, "name", "").lower() == name.lower():
                return getattr(v, "voice_id")
    except Exception:
        pass
    # Fallback premade voice by character type
    return _pick_fallback_voice_id(type_)


def _synthesize_line_stream(client: ElevenLabs, voice_id: str, text: str, settings: VoiceSettings):
    """Return a streaming generator of audio bytes from ElevenLabs."""
    return client.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_44100_128",
        text=text,
        voice_settings=settings,
    )


def _safe_filename(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum() or ch in ("-", "_")) or "untitled"


def generate_dialogues(storyline_path: Optional[str] = None, force: bool = False) -> str:
    """
    Generate MP3 files for all dialogue lines into game/assets/dialogues using appropriate voices per character.

    Parameters:
    - storyline_path: optional override path to storyline JSON
    - force: re-generate files even if they already exist
    """
    project_root = Path(__file__).resolve().parents[2]
    output_root = project_root / "game" / "assets" / "dialogues"
    output_root.mkdir(parents=True, exist_ok=True)

    # Load storyline
    story_file = Path(storyline_path) if storyline_path else _find_storyline_file()
    if not story_file.exists():
        raise FileNotFoundError(f"Storyline file not found: {story_file}")
    story = _load_storyline(story_file)

    # Build character registry
    characters = _collect_characters(story)
    name_to_meta = {c["name"].lower(): c for c in characters}

    # Prepare client
    client = _get_elevenlabs_client()

    # Cache voice selections
    name_to_voice_id: Dict[str, str] = {}
    name_to_settings: Dict[str, VoiceSettings] = {}

    # Resolve voices for all characters upfront
    for c in characters:
        cname = c["name"].strip()
        ctype = c["type"]
        cmood = c.get("mood", "")
        vid = _get_or_create_voice_id(client, cname, ctype, cmood)
        name_to_voice_id[cname.lower()] = vid
        name_to_settings[cname.lower()] = _voice_settings_for(ctype, cmood)

    # Collect lines
    lines = _collect_dialogue_lines(story)

    generated_count = 0
    skipped_count = 0

    for idx, (speaker, text, group) in enumerate(lines, start=1):
        speaker_key = speaker.lower()
        meta = name_to_meta.get(speaker_key)
        # If the speaker isn't a known character, treat as narrator with male voice
        if meta is None:
            meta = {"name": speaker, "type": "male", "mood": "stoic"}
            if speaker_key not in name_to_voice_id:
                name_to_voice_id[speaker_key] = _pick_fallback_voice_id("male")
                name_to_settings[speaker_key] = _voice_settings_for("male", "stoic")

        # Resolve voice/settings
        voice_id = name_to_voice_id.get(speaker_key) or _pick_fallback_voice_id(meta["type"])
        settings = name_to_settings.get(speaker_key) or _voice_settings_for(meta["type"], meta.get("mood", ""))

        # Output path
        char_dir = output_root / _safe_filename(speaker)
        group_dir = char_dir / _safe_filename(group)
        group_dir.mkdir(parents=True, exist_ok=True)
        file_path = group_dir / f"line_{idx:03d}.mp3"

        if file_path.exists() and not force:
            skipped_count += 1
            continue

        # Synthesize (stream chunks to file)
        stream = _synthesize_line_stream(client, voice_id, text, settings)
        with open(file_path, "wb") as f:
            for chunk in stream:
                if not chunk:
                    continue
                # ElevenLabs SDK yields bytes; be defensive just in case
                if isinstance(chunk, (bytes, bytearray)):
                    f.write(chunk)
                else:
                    try:
                        data = bytes(chunk)
                        f.write(data)
                    except Exception:
                        # Skip unexpected chunk types silently
                        continue
        generated_count += 1

    return f"Dialogue generation complete. Generated: {generated_count}, skipped: {skipped_count}. Output: {output_root}"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate dialogues with ElevenLabs")
    parser.add_argument("--storyline", type=str, default=None, help="Path to storyline JSON")
    parser.add_argument("--force", action="store_true", help="Overwrite existing audio files")
    args = parser.parse_args()

    try:
        msg = generate_dialogues(args.storyline, force=args.force)
        print(msg)
    except Exception as e:
        print(f"Error: {e}")
        raise


