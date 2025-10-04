from typing import Optional, Dict, Any, List
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

async def refine_prompt(openai, prompt: str) -> str:

    with open("mcp_server/tools/sample_storyline.txt", "r") as f:
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

        Return a JSON object with the following structure:

        "main_character": {{
            "type": "object",
            "properties": {{
                "id": {{ "type": "string" }},
                "name": {{ "type": "string" }},
                "description": {{ "type": "string" }},
                "class": {{ "type": "string" }},
                "race": {{ "type": "string" }},
                "level": {{ "type": "integer" }},
                "stats": {{
                "type": "object",
                "properties": {{
                    "strength": {{ "type": "integer" }},
                    "dexterity": {{ "type": "integer" }},
                    "intelligence": {{ "type": "integer" }},
                    "charisma": {{ "type": "integer" }},
                    "luck": {{ "type": "integer" }}
                }}
                }},
                "skills": {{
                "type": "array",
                "items": {{
                    "type": "object",
                    "properties": {{
                    "name": {{ "type": "string" }},
                    "description": {{ "type": "string" }},
                    "level": {{ "type": "integer" }},
                    "requirements": {{ "type": "array", "items": {{ "type": "string" }} }}
                    }}
                }}
                }},
                "inventory": {{ "type": "array", "items": {{ "type": "string" }} }},
                "equipment": {{
                "type": "object",
                "properties": {{
                    "weapon": {{ "type": "string" }},
                    "armor": {{ "type": "string" }},
                    "accessory": {{ "type": "string" }}
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

async def generate_characters(context, openai, prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
        Generate a character list for a game based on the following user prompt: {prompt}

        Return a JSON object with the following structure:
        
        **DO NOT INCLUDE THE MAIN CHARACTER**

        "characters": {{
            "type": "array",
            "items": {{
                "type": "object",
                "properties": {{
                "id": {{ "type": "string" }},
                "name": {{ "type": "string" }},
                "role": {{ "type": "string" }},
                "description": {{ "type": "string" }},
                "abilities": {{ "type": "array", "items": {{ "type": "string" }} }},
                "mood": {{ "type": "string" }}
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

async def generate_scenes(context, openai,prompt: str) -> List[Dict[str, Any]]:
    prompt_text = f"""
        Generate a list of 5 scenes for a game based on the following user prompt: {prompt}

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
        ctx.log("🔄 Starting storyline pipeline...")

    storyline = await generate_initial_storyline(prompt, ctx=ctx)
    
    json_string = json.dumps(storyline, indent=2)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json_string)

    if ctx:
        ctx.log("✅ Storyline pipeline complete.")

    return {
        "storyline": storyline,
        "json_string": json.dumps(storyline, indent=2)
    }
