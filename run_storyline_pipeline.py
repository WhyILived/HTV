import asyncio
import sys
from typing import Optional

from mcp_server.tools.storyline_pipeline import build_storyline_pipeline


async def main(prompt: Optional[str] = None) -> None:
    if not prompt:
        # Default prompt explicitly references Interstellar to encourage accurate adaptation
        prompt = "Create an accurate 2D pixel-art game adaptation of the movie Interstellar."

    try:
        result = await build_storyline_pipeline(prompt)
        output_path = result.get("output_path", "storyline.json") if isinstance(result, dict) else "storyline.json"
        print(f"✅ Storyline generated and saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    user_prompt = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else None
    asyncio.run(main(user_prompt))


