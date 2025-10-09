from typing import Optional, Dict, Any, List
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

async def get_response(openai, prompt: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=1
    )

    return response.choices[0].message.content

async def refine_prompt(openai, prompt: str) -> str:

    with open("mcp_server/tools/sample_storyline.txt", "r", encoding="utf-8") as f:
        example_txt = f.read()

    prompt_text = f"""
        Generate a refined version of the following prompt that will generate one component of the storyline for a game: {prompt}
        
        For more context, this component will be included in a larger JSON structure that represents the full game storyline. Here is an example of a
        JSON structure for a game storyline: {example_txt}
        """
        
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    return response.choices[0].message.content

async def generate_game_overview(context, openai: OpenAI, prompt: str) -> Dict[str, Any]:
    prompt_text = f"""
Generate a detailed game overview for a 2D pixel-style game based on the following user concept: {prompt}

GUIDELINES:
1. Determine Intent:
   - If the user prompt references an existing movie, show, myth, or historical figure, treat it as a request for an ACCURATE but engaging depiction of that story or character.
   - If the prompt is fully original, generate a CREATIVE and imaginative storyline inspired by its theme.

2. Accuracy & Creativity:
   - When accuracy is required, stay true to the known story, setting, and characters while adapting them into interactive, game-suitable form (levels, conflicts, player goals, etc.).
   - When originality is required, expand creatively with new world-building elements, distinctive tone, and clear player motivations.
   - You may include spoilers and reinterpretations when relevant. This content is for CREATIVE GAME DEVELOPMENT purposes only.

3. Tone & Style:
   - Write as if describing a GAME PITCH DOCUMENT for developers and artists.
   - Keep the tone vivid and concrete, consistent with a 2D pixel-art world.
   - Avoid filler text, opinions, or meta-commentary.

Return a JSON object with the following structure:

{{
    "game": {{
        "title": "string - concise, appealing game title. If its a show, movie, book, fairy tale or anything that exists, include the name as the title",
        "genre": "string - e.g. adventure, puzzle-platformer, RPG, simulation, etc.",
        "plot": "string - 25-30 sentences summarizing the player's main goal and the plot of the game",
        "reference_media": "string - if the user prompt is based on an existing medium, include the name of the medium as the reference_media, for example 'Interstellar' or 'The Matrix' or 'The Lord of the Rings' if the user prompt is based on those explicitly. If no reference media is mentioned, include 'None'"
    }}
}}
"""

        
    # prompt_text = await refine_prompt(openai, prompt_text)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    return json.loads(response.choices[0].message.content)

async def generate_main_character(context, openai, prompt: str) -> Dict[str, Any]:
    prompt_text = f"""
Generate a MAIN CHARACTER for a 2D pixel-style game using the following user concept: {prompt}.

You also have prior context from the game overview (title/genre/summary/world_setting): 
{json.dumps(context, indent=2)}

GUIDELINES (concise):
- Consistency: Align character tone, gear, and abilities with the game's genre and world_setting. No anachronisms unless the prompt implies them.
- Visual vs Lore split: Put ONLY appearance/clothing/accessories in visual_description (no backstory, no abilities).
- Gameplay-first: Stats/skills must produce a clear playstyle. Skills should be actionable in-game verbs (dash, parry, freeze, hack), not vague traits.
- Compact & Valid: Keep names concise, era-appropriate. Keep JSON valid (no comments) and return ONLY the JSON object.

FIELD RULES (for the model; do NOT include in output):
- name: natural, setting-appropriate display name.
- type: one of ["male", "female", "robot"].
- visual_description: 1–3 sentences; pixel-art friendly descriptors (palette hints, silhouette features, notable accessories).
- class: concise archetype (e.g., "ice mage", "rogue archer", "tinkerer").
- race: setting-fitting (e.g., "human", "elf", "automaton"); use "human" if historical/realistic.
- level: integer 1–10 (start power).
- stats: integers 1–10 each; total between 35–45 across strength, dexterity, intelligence, charisma, luck.
- skills: 2–5 items; each with name, clear 1–2 sentence description (mechanics), level 1–5, and requirements referencing level/stats/equipment as simple strings.
- inventory: 3–8 thematically consistent items (consumables, tools, quest items).
- equipment: exactly one weapon, one armor, one accessory; must also appear in inventory.

Return ONLY a JSON object (no prose, no markdown) with EXACTLY these fields:

The main character should be ONE character only.

{{"main_character": {{
  "name": "string",                        # display name
  "type": "male" | "female" | "robot" | "misc",     # one of the allowed values
  "visual_description": "string",          # appearance/clothing/accessories only
  "class": "string",                       # concise archetype
  "level": "integer",                      # starts at 1 and increases as the player progresses
  "stats": {{                             # 35–45 total; each 1–10
    "strength": "integer",
    "dexterity": "integer",
    "intelligence": "integer",
    "charisma": "integer",
    "luck": "integer"
  }},
  "dialogue": [],
  "inventory": {{
      "weapons": [],
      "armor": [],
      "accessories": []
    }}
}}
}}
"""


        
    # prompt_text = await refine_prompt(openai, prompt_text)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    result = json.loads(response.choices[0].message.content)

    # Mutate earlier JSON (game plot) if the chosen main character meaningfully changes perspective
    try:
        # Expect structure: context["game"]["game"]["plot"], and main character at result["main_character"]
        game_container: Dict[str, Any] = context.get("game", {}) if isinstance(context, dict) else {}
        game_meta: Dict[str, Any] = game_container.get("game", {}) if isinstance(game_container, dict) else {}
        plot_text: Any = game_meta.get("plot")
        reference_media: Any = game_meta.get("reference_media")

        main_char: Dict[str, Any] = result.get("main_character", {}) if isinstance(result, dict) else {}
        name: Any = main_char.get("name")
        char_class: Any = main_char.get("class")

        def is_non_none_media(value: Any) -> bool:
            return isinstance(value, str) and value.strip().lower() != "none"

        # Decide if plot should be updated: when the selected main character is not already reflected in the plot
        should_update = (
            isinstance(plot_text, str)
            and isinstance(name, str)
            and name not in plot_text
        )

        if should_update:
            addition_parts: list[str] = []
            # Add a concise perspective note referencing the main character
            if isinstance(char_class, str) and char_class.strip():
                addition_parts.append(f"The story is presented through {name}, a {char_class}.")
            else:
                addition_parts.append(f"The story is presented through {name}.")

            # If based on existing media, explicitly keep events faithful to the source
            if is_non_none_media(reference_media):
                addition_parts.append(f"Events remain faithful to {reference_media}.")

            addition_sentence = " " + " ".join(addition_parts)

            # Ensure proper spacing/punctuation when appending
            updated_plot = (plot_text.rstrip() + ("" if plot_text.rstrip().endswith(('.', '!', '?')) else ".") + addition_sentence)

            game_meta["plot"] = updated_plot
            game_container["game"] = game_meta
            if isinstance(context, dict):
                context["game"] = game_container
    except Exception:
        # Best-effort mutation; avoid failing the generator if structure differs
        pass

    return result

async def generate_characters(context, openai, prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
Generate SUPPORTING CHARACTERS for a 2D pixel-style game using this concept: {prompt}.
You also have prior context from the game overview/main character: {json.dumps(context, indent=2)}

GUIDELINES (concise):
- Exclude the main character entirely (no duplicate name/class/role from context).
- Cohesion: Roles, outfits, and abilities must fit the game's genre and world_setting; avoid anachronisms unless implied.
- Cast variety: Include a mix of functions (e.g., mentor, rival, quest-giver, vendor, healer, engineer, comic relief, antagonist lieutenant).
- Pixel-art friendly: Visuals should be silhouette- and palette-aware, 1–2 sentences only (no lore/abilities).
- Compact & Valid: Return ONLY a JSON array; keep each object tight and actionable.

FIELD RULES (for the model; do NOT include in output):
- name: setting-appropriate display name.
- role: concise functional label (e.g., "quest-giver", "blacksmith", "antagonist-lieutenant").
- type: one of ["male", "female", "robot"].
- visual_description: 1–2 sentences; appearance/clothing/accessories only.
- dialogue: a DICTIONARY keyed by act number to a list of dialogue lines; keep it EMPTY for now (e.g., {{}}). It will be filled later.
- mood: pick one from ["loyal", "grumpy", "mysterious", "optimistic", "stoic", "scheming", "witty", "anxious", "brave"].

Return ONLY a JSON array (no prose/markdown) of 5–7 character objects, each with EXACTLY these fields:

{{ "characters": [
  {{
    "name": "string",               // display name
    "role": "string",               // functional role in gameplay
    "type": "male" | "female" | "robot",
    "visual_description": "string", // appearance/clothing/accessories only
    "dialogue": [],                 // empty list for now; will be filled later per act
    "mood": "string"                // choose from the allowed list
  }}
]}}
"""

        
    # prompt_text = await refine_prompt(openai, prompt_text)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    return json.loads(response.choices[0].message.content)

async def generate_act(context, openai, prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
        Generate the FIRST THREE ACTS for a 2D pixel-style game, based on the PLOT below. Each act must represent at least 10% of the plot's progression and be coherent by itself.

        REQUIREMENTS:
        1) id: 1, 2, 3 (sequential)
        2) title: "Act <id>: <catchy concise title>" (e.g., "Act 1: It begins...")
        3) setting: short, concrete scene description
        4) characters: list of EXACT character display names drawn ONLY from the character data below (including the main character when relevant). No new names.
        5) dialogue: an ordered list of objects where the FIRST item is a QUESTION and the subsequent items are RESPONSES. Each item has {{"speaker": "ExactName", "line": "string"}}. Keep lines concise.
        6) interaction: for each act, include an object {{"asker": "ExactName", "addressee": "ExactName", "answer_options": ["string", ...]}}. The answer_options are the player's possible answers to the FIRST question.

        Return ONLY a JSON object with EXACTLY this structure:

        {{
          "acts": [
            {{
              "id": 1,
              "title": "Act 1: <catchy title>",
              "setting": "string",
              "characters": ["ExactName", "ExactName"],
              "dialogue": [{{"speaker": "ExactName", "line": "question?"}}, {{"speaker": "ExactName", "line": "response"}}],
              "interaction": {{"asker": "ExactName", "addressee": "ExactName", "answer_options": ["opt1", "opt2"]}}
            }},
            {{
              "id": 2,
              "title": "Act 2: <catchy title>",
              "setting": "string",
              "characters": ["ExactName"],
              "dialogue": [{{"speaker": "ExactName", "line": "question?"}}, {{"speaker": "ExactName", "line": "response"}}],
              "interaction": {{"asker": "ExactName", "addressee": "ExactName", "answer_options": ["opt1", "opt2"]}}
            }},
            {{
              "id": 3,
              "title": "Act 3: <catchy title>",
              "setting": "string",
              "characters": ["ExactName"],
              "dialogue": [{{"speaker": "ExactName", "line": "question?"}}, {{"speaker": "ExactName", "line": "response"}}],
              "interaction": {{"asker": "ExactName", "addressee": "ExactName", "answer_options": ["opt1", "opt2"]}}
            }}
          ]
        }}

        CONTEXT (use faithfully; do NOT invent new names):
        {json.dumps(context, indent=2)}
        """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    result = json.loads(response.choices[0].message.content)

    # Best-effort normalization and cross-linking with characters
    try:
        storyline_dict: Dict[str, Any] = context if isinstance(context, dict) else {}
        # Build set of valid character names (main + supporting)
        valid_names: set[str] = set()
        main_obj: Dict[str, Any] = storyline_dict.get("main_character", {}) if isinstance(storyline_dict, dict) else {}
        main_char: Dict[str, Any] = main_obj.get("main_character", {}) if isinstance(main_obj, dict) else {}
        if isinstance(main_char.get("name"), str):
            valid_names.add(main_char["name"])
        chars_obj: Dict[str, Any] = storyline_dict.get("characters", {}) if isinstance(storyline_dict, dict) else {}
        char_list: List[Dict[str, Any]] = chars_obj.get("characters", []) if isinstance(chars_obj, dict) else []
        name_to_char: Dict[str, Dict[str, Any]] = {}
        for ch in char_list:
            if isinstance(ch, dict) and isinstance(ch.get("name"), str):
                valid_names.add(ch["name"])
                name_to_char[ch["name"]] = ch

        acts: List[Dict[str, Any]] = result.get("acts", []) if isinstance(result, dict) else []

        # Ensure IDs and titles normalized; filter character lists to valid names
        for idx, act in enumerate(acts, start=1):
            if isinstance(act, dict):
                act["id"] = idx
                title: str = act.get("title") or ""
                if not isinstance(title, str) or not title.strip().lower().startswith(f"act {idx}:"):
                    short = title.strip() if isinstance(title, str) else ""
                    act["title"] = f"Act {idx}: {short or 'Untitled'}"
                char_names = [n for n in (act.get("characters") or []) if isinstance(n, str) and n in valid_names]
                # Ensure main character appears when relevant (if present in valid_names but not listed, we don't force; keep light)
                act["characters"] = char_names

        # Populate per-act dialogue lists for both the asker and MAIN CHARACTER
        def ensure_dialogue_list(obj: Dict[str, Any], size: int) -> None:
            if not isinstance(obj.get("dialogue"), list):
                obj["dialogue"] = []
            while len(obj["dialogue"]) < size:
                obj["dialogue"].append({})

        # Determine main character name and object
        main_name: str = main_char.get("name") if isinstance(main_char.get("name"), str) else ""
        main_obj_ref: Dict[str, Any] = main_char

        for act in acts:
            if not isinstance(act, dict):
                continue
            interaction = act.get("interaction") or {}
            asker = interaction.get("asker")
            addressee = interaction.get("addressee")
            options = interaction.get("answer_options") or []
            act_id = act.get("id")

            # Enforce addressee is main character
            if isinstance(main_name, str) and main_name and addressee != main_name:
                interaction["addressee"] = main_name
                addressee = main_name

            # If the asker is the main character (or missing), pick a different valid character from this act
            if (not isinstance(asker, str)) or (asker == main_name):
                act_chars = act.get("characters") if isinstance(act.get("characters"), list) else []
                replacement = next((n for n in act_chars if isinstance(n, str) and n != main_name and n in name_to_char), None)
                if replacement is None:
                    # fallback: any supporting character
                    replacement = next((n for n in name_to_char.keys() if n != main_name), None)
                if isinstance(replacement, str):
                    interaction["asker"] = replacement
                    asker = replacement

            # Normalize act dialogue: first is a question by asker, subsequent responses by main character
            dlg = act.get("dialogue")
            if isinstance(dlg, list) and dlg:
                # Ensure first entry is from asker
                first = dlg[0]
                if isinstance(first, dict):
                    first["speaker"] = asker if isinstance(asker, str) else first.get("speaker")
                    if isinstance(first.get("line"), str) and not first["line"].strip().endswith("?"):
                        first["line"] = first["line"].rstrip(" .!") + "?"
                # Ensure responses are from main character
                for i in range(1, len(dlg)):
                    if isinstance(dlg[i], dict):
                        dlg[i]["speaker"] = main_name or dlg[i].get("speaker")

            if isinstance(asker, str) and isinstance(addressee, str) and isinstance(act_id, int) and act_id > 0:
                # Update asker's per-act dialogue
                asker_obj = name_to_char.get(asker)
                if asker_obj is not None:
                    ensure_dialogue_list(asker_obj, act_id)
                    asker_obj["dialogue"][act_id - 1] = {addressee: options if isinstance(options, list) else []}

                # Update main character's per-act dialogue
                if isinstance(main_obj_ref, dict) and main_name:
                    ensure_dialogue_list(main_obj_ref, act_id)
                    main_obj_ref["dialogue"][act_id - 1] = {asker: options if isinstance(options, list) else []}

        # Persist the possibly mutated characters and main character back into context
        if isinstance(context, dict):
            context["characters"] = {"characters": char_list}
            context["main_character"] = {"main_character": main_obj_ref}

    except Exception:
        pass

    return result

async def generate_skill_tree(context, openai, prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
        Generate a skill tree for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed.

        Return a JSON object with the following structure:

        "skill_tree": [
        {{
            "branch": "string",
            "skills": [
            {{
                "name": "string",
                "effect": "string",
                "requirements": ["string", ...]
            }}
            ]
        }}
        ]
        
        Here is more context on what has already been generated: {json.dumps(context, indent=2)}
        """
        
    # prompt_text = await refine_prompt(openai, prompt_text)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    return json.loads(response.choices[0].message.content)

async def generate_weapons(context, openai, prompt: str) -> Dict[str, Any]:
    prompt_text = f"""
        Generate a list of weapons for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed.

        Return a JSON object with the following structure:

        "weapons": [
            {{
                "name": "string",
                "description": "string",
                "damage": number,
                "requirements": ["string", ...]
            }}
        ]
        
        Here is more context on what has already been generated: {json.dumps(context, indent=2)}
        """
        
    # prompt_text = await refine_prompt(openai, prompt_text)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    return json.loads(response.choices[0].message.content)

async def generate_cutscenes(context, openai, prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
        Generate a list of 3 cutscenes for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed. Include spoilers and plot details as needed for the game.

        Return a JSON object with the following structure:

        "cutscenes": [
                {{
                    "id": number,
                    "title": "string",
                    "description": "string",
                    "dialogue": [
                        {{
                            "speaker": "string",
                            "line": "string"
                        }}
                    ]
                }}
        ]
            
        Here is more context on what has already been generated: {json.dumps(context, indent=2)}
        """
        
    # prompt_text = await refine_prompt(openai, prompt_text)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    return json.loads(response.choices[0].message.content)

# ----- Main Storyline Generator -----
async def generate_initial_storyline(prompt: str, ctx: Optional[Any] = None) -> Dict[str, Any]:
    if ctx:
        ctx.log(f"Generating storyline for prompt: {prompt}")
        
    openai = OpenAI()
    
    # Use a single shared dict so later generators can mutate earlier sections
    storyline: Dict[str, Any] = {}

    game = await generate_game_overview(storyline, openai, prompt)
    storyline["game"] = game

    main_character = await generate_main_character(storyline, openai, prompt)
    storyline["main_character"] = main_character

    characters = await generate_characters(storyline, openai, prompt)
    storyline["characters"] = characters

    acts = await generate_act(storyline, openai, prompt)
    storyline["acts"] = acts
    # Compatibility shim: project acts into legacy scenes shape for downstream consumers
    try:
        acts_list = acts.get("acts", []) if isinstance(acts, dict) else []
        projected_scenes = []
        for act in acts_list:
            if isinstance(act, dict):
                projected_scenes.append({
                    "id": act.get("id"),
                    "title": act.get("title"),
                    "setting": act.get("setting"),
                    "characters": act.get("characters", [])
                })
        storyline["scenes"] = {"scenes": projected_scenes}
    except Exception:
        pass

    skill_tree = await generate_skill_tree(storyline, openai, prompt)
    storyline["skill_tree"] = skill_tree

    weapons = await generate_weapons(storyline, openai, prompt)
    storyline["weapons"] = weapons

    cutscenes = await generate_cutscenes(storyline, openai, prompt)
    storyline["cutscenes"] = cutscenes

    if ctx:
        ctx.log("Storyline generation complete.")
    return storyline

# ----- Storyline Pipeline -----
async def build_storyline_pipeline(prompt: str, ctx: Optional[Any] = None, output_file: str = "storyline.json") -> Dict[str, Any]:
    if ctx:
        ctx.log("Starting storyline pipeline...")

    storyline = await generate_initial_storyline(prompt, ctx=ctx)
    
    json_string = json.dumps(storyline, indent=2)
    
    # Always write to project root so users can easily find the file
    project_root = Path(__file__).resolve().parents[2]
    output_path = (project_root / output_file).resolve()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_string)

    if ctx:
        ctx.log("Storyline pipeline complete.")

    return {
        "storyline": storyline,
        "output_path": str(output_path)
    }
