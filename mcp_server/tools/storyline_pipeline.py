from typing import Optional, Dict, Any, List
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

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
        "summary": "string - 2-4 sentences summarizing the player's main goal and core loop",
        "world_setting": "string - describe the world's atmosphere, locations, and tone in detail"
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
- id: short, URL-safe slug; all lowercase; hyphens allowed (e.g., "elsa-arendelle-scout").
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

{{"main_character": {{
  "id": "string",                          # short slug (lowercase, hyphens)
  "name": "string",                        # display name
  "type": "male" | "female" | "robot",     # one of the allowed values
  "visual_description": "string",          # appearance/clothing/accessories only
  "class": "string",                       # concise archetype
  "level": "integer",                      # 1–10
  "stats": {{                             # 35–45 total; each 1–10
    "strength": "integer",
    "dexterity": "integer",
    "intelligence": "integer",
    "charisma": "integer",
    "luck": "integer"
  }},
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

    return json.loads(response.choices[0].message.content)

async def generate_characters(context, openai, prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
Generate SUPPORTING CHARACTERS for a 2D pixel-style game using this concept: {prompt}.
You also have prior context from the game overview/main character: {json.dumps(context, indent=2)}

GUIDELINES (concise):
- Exclude the main character entirely (no duplicate name/id/class/role from context).
- Cohesion: Roles, outfits, and abilities must fit the game's genre and world_setting; avoid anachronisms unless implied.
- Cast variety: Include a mix of functions (e.g., mentor, rival, quest-giver, vendor, healer, engineer, comic relief, antagonist lieutenant).
- Pixel-art friendly: Visuals should be silhouette- and palette-aware, 1–2 sentences only (no lore/abilities).
- Compact & Valid: Return ONLY a JSON array; keep each object tight and actionable.

FIELD RULES (for the model; do NOT include in output):
- id: short, URL-safe slug; lowercase with hyphens; unique across the array and distinct from main character.
- name: setting-appropriate display name.
- role: concise functional label (e.g., "quest-giver", "blacksmith", "antagonist-lieutenant").
- type: one of ["male", "female", "robot"].
- visual_description: 1–2 sentences; appearance/clothing/accessories only.
- dialogue: 3 concise, to the point dialogues for the main character to interact with
- mood: pick one from ["loyal", "grumpy", "mysterious", "optimistic", "stoic", "scheming", "witty", "anxious", "brave"].

Return ONLY a JSON array (no prose/markdown) of 5–7 character objects, each with EXACTLY these fields:

{{ "characters": [
  {{
    "id": "string",                 // lowercase, hyphenated slug; unique
    "name": "string",               // display name
    "role": "string",               // functional role in gameplay
    "type": "male" | "female" | "robot",
    "visual_description": "string", // appearance/clothing/accessories only
    "dialogue": [],                 // list of strings of dialogue
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

async def generate_scenes(context, openai,prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
        Generate a list of 5 scenes for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed. Include spoilers and plot details as needed for the game.

        Return a JSON object with the following structure:

        "scenes": {{
            "id": "integer",
            "title": "string",
            "setting": "string",
            "characters": []
            }},
            
        Here is more context on what has already been generated: {json.dumps(context, indent=2)}
        """
        
    # prompt_text = await refine_prompt(openai, prompt_text)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=1
    )

    return json.loads(response.choices[0].message.content)

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
                "id": "string",
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
    
    context = []

    game = await generate_game_overview(context, openai, prompt)
    context.append(game)
    main_character = await generate_main_character(context, openai, prompt)
    context.append(main_character)
    characters = await generate_characters(context, openai, prompt)
    context.append(characters)
    scenes = await generate_scenes(context, openai, prompt)
    context.append(scenes)
    skill_tree = await generate_skill_tree(context, openai, prompt)
    context.append(skill_tree)
    weapons = await generate_weapons(context, openai, prompt)
    context.append(weapons)
    cutscenes = await generate_cutscenes(context, openai, prompt)
    context.append(cutscenes)

    storyline = {
        "game": game,
        "main_character": main_character,
        "characters": characters,
        "scenes": scenes,
        "skill_tree": skill_tree,
        "weapons": weapons,
        "cutscenes": cutscenes,
    }

    if ctx:
        ctx.log("Storyline generation complete.")
    return storyline

# ----- Storyline Pipeline -----
async def build_storyline_pipeline(prompt: str, ctx: Optional[Any] = None, output_file: str = "storyline.json") -> Dict[str, Any]:
    if ctx:
        ctx.log("Starting storyline pipeline...")

    storyline = await generate_initial_storyline(prompt, ctx=ctx)
    
    json_string = json.dumps(storyline, indent=2)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json_string)

    if ctx:
        ctx.log("Storyline pipeline complete.")

    return storyline
