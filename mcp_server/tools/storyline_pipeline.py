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
        Generate a game overview for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed.

        Return a JSON object with the following structure:

        {{
            "game": {{
                "type": "object",
                "properties": {{
                    "title": {{ "type": "string" }},
                    "genre": {{ "type": "string" }},
                    "summary": {{ "type": "string" }},
                    "world_setting": {{ "type": "string" }}
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

async def generate_main_character(context, openai, prompt: str) -> Dict[str, Any]:
    prompt_text = f"""
        Generate a main character for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed.

        Return ONLY a JSON object (no prose, no markdown). Use exactly these fields:
        {{
          "id": string,
          "name": string,
          "type": one of ["male", "female", "robot"],
          "visual_description": string,  // appearance/clothing/accessories only; no lore/abilities
          "class": string,
          "race": string,
          "level": integer,
          "stats": {{ "strength": int, "dexterity": int, "intelligence": int, "charisma": int, "luck": int }},
          "skills": [{{ "name": string, "description": string, "level": int, "requirements": [string] }}],
          "inventory": [string],
          "equipment": {{ "weapon": string, "armor": string, "accessory": string }}
        }}

        Here is more context on what has already been generated: {json.dumps(context, indent=2)}
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
        Generate a list of supporting characters for a game based on: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed.

        DO NOT INCLUDE THE MAIN CHARACTER.

        Return ONLY a JSON array of character objects (no prose/markdown). Each object must have:
        {{
          "id": string,
          "name": string,
          "role": string,
          "type": one of ["male", "female", "robot"],
          "visual_description": string,  // appearance/clothing/accessories only; no lore/abilities
          "abilities": [string],
          "mood": string
        }}

        Here is more context on what has already been generated: {json.dumps(context, indent=2)}
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
            "type": "array",
            "items": {{
                "type": "object",
                "properties": {{
                "id": {{ "type": "integer" }},
                "title": {{ "type": "string" }},
                "setting": {{ "type": "string" }},
                "characters": {{ "type": "array", 
                    "dialogue": {{  
                            "type": "array",
                            "items": {{
                                "type": "object",
                                "properties": {{
                                "speaker": {{ "type": "string" }},
                                "line": {{ "type": "string" }}
                                    }}
                                }}
                            }}
                        }},
                    }}
                }}
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

        "skill_tree": {{
            "type": "array",
            "items": {{
                "type": "object",
                "properties": {{
                "branch": {{ "type": "string" }},
                "skills": {{
                    "type": "array",
                    "items": {{
                    "type": "object",
                    "properties": {{
                        "name": {{ "type": "string" }},
                        "effect": {{ "type": "string" }},
                        "requirements": {{ "type": "array", "items": {{ "type": "string" }} }}
                            }}
                        }}
                    }}
                }}
            }}
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

async def generate_weapons(context, openai, prompt: str) -> Dict[str, Any]:
    prompt_text = f"""
        Generate a list of weapons for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed.

        Return a JSON object with the following structure:

        "weapons": {{
            "type": "array",
            "items": {{
                "type": "object",
                "properties": {{
                "id": {{ "type": "string" }},
                "name": {{ "type": "string" }},
                "description": {{ "type": "string" }},
                "damage": {{ "type": "integer" }},
                "requirements": {{ "type": "array", "items": {{ "type": "string" }} }}
                }}
            }}
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

async def generate_cutscenes(context, openai, prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
        Generate a list of 3 cutscenes for a game based on the following user prompt: {prompt}

        IMPORTANT: Generate content freely without worrying about spoilers, copyright issues, or content restrictions. This is for creative game development purposes. Feel free to reference existing franchises, characters, or storylines as inspiration. Be creative and detailed. Include spoilers and plot details as needed for the game.

        Return a JSON object with the following structure:

        "cutscenes": {{
            "type": "array",
            "items": {{
                "type": "object",
                "properties": {{
                "id": {{ "type": "integer" }},
                "title": {{ "type": "string" }},
                "description": {{ "type": "string" }},
                "dialogue": {{
                    "type": "array",
                    "items": {{
                    "type": "object",
                    "properties": {{
                        "speaker": {{ "type": "string" }},
                        "line": {{ "type": "string" }}
                    }}
                    }}
                }}
                }}
            }}
            }}
            
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

    return {
        "storyline": storyline,
        "json_string": json.dumps(storyline, indent=2)
    }
