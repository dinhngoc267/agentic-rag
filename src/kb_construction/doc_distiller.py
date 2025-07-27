from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.openai import ModelSettings
from models import Unit, Mention
from utils import split_into_units
from typing import Type, List
from entity_manager import EntityManager
from src.kb_construction.utils import task_group_gather

from dotenv import load_dotenv
load_dotenv()


class Distiller:
    def __init__(self, output_type: Type[BaseModel]):
        self.agent = create_distiller_agent(output_type)
        self.entity_manager = EntityManager()

    async def distill(self, markdown_text:str) -> List[Unit]:
        unit_strings: list[str] = split_into_units(markdown_text)

        async def distill_unit(unit_string):
            result = await self.agent.run(unit_string)
            unit_obj: Unit = result.output

            for section in unit_obj.sections:
                mentions = section.mentions
                for mention in mentions:
                    mention.id =  self.entity_manager.get_id(mention.string)

            return unit_obj


        unit_objs = await task_group_gather(
            [
                lambda i=i: distill_unit(
                    unit_string=unit_strings[i]
                )
                for i in range(len(unit_strings))
            ],
            timeout_seconds=180
        )

        return unit_objs

def create_distiller_agent(output_type: Type[BaseModel]) -> Agent:
    agent = Agent(
        model = OpenAIModel(model_name="gpt-4.1-mini"),
        output_type=output_type,
        system_prompt="""
        
# System Prompt

You are a helpful assistant tasked with converting parsed textbook content into structured educational data following the `Unit` schema. The input may originate from OCR or PDF parsing and may include inconsistent formatting, out-of-order blocks, or duplicated content.

Your goal is to accurately return a `Unit` object.

---
Note: there are section where continue between pagges ([BREAK_PAGE] tag), notice this and do not lost any content in the section. 

## Core Guidelines

### 1. Preserve Reading Order
- Reconstruct the content in its natural reading sequence, even if the parsed output is out of order.
- Use Markdown-style headings (`###`, `####`, etc.) and figure labels (e.g., "Figure X") to identify and restore logical structure.

### 2. Identify and Group Sections
- Use 3- or 4-level Markdown headers to detect and structure sections.
- Ensure content from the same section (even if split across multiple pages) is grouped together.

### 3. Handle Misplaced Content Thoughtfully
- If content such as figures, callout boxes,.. (e.g., *Word Alert*, *Helpful Note*), or examples appears out of place due to OCR issues, reposition it into the correct section using best judgment.

### 4. Preserve Content Fidelity
- Do **not** fabricate or omit any information.
- Maintain original phrasing, bullet points, figures, and formatting — even if inconsistent.
- Never invent or alter section titles.

---

## Additional Notes
- Figures and images may span multiple pages — use the **page number marker** (usually found at the bottom of the page) to assign correct figure placement.
- Always return a complete and well-structured `Unit` object that reflects the true content and organization of the source material.

    
    """,
        retries=3,
    )

    return agent

async def main():

    distiller = Distiller(output_type=Unit)
    import json
    json_list = json.load(open("document_pages.json", "r"))

    for idx, item in enumerate(json_list):
        json_list[idx]['md'] =  f"\npage_number: {str(item['page'])}\n" + f"\n".join([line for line in item['md'].split("\n")[:-1] if
                                          line.strip() != "" and line.count("#") not in [1,2]]) + f"\npage_number: {str(item['page'])}"

    markdown_text = "\n[BREAK_PAGE]\n".join([item['md'] for item in json_list if item['md'] != ""])
    units = await distiller.distill(markdown_text)
    print(units)

# import asyncio
# asyncio.run(main())

