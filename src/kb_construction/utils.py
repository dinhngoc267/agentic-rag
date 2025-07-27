import os
from dotenv import load_dotenv
load_dotenv()
from typing import Callable, Awaitable, Sequence, TypeVar, Optional
import asyncio
import anyio
T = TypeVar("T")

async def task_group_gather(tasks: Sequence[Callable[[], Awaitable[T]]],
                            timeout_seconds:int =120) -> list[Optional[T]]:
    results: list[Optional[T]] = [None] * len(tasks)
    max_retries = 5

    async def _run_task(task_fn: Callable[[], Awaitable[T]], index: int):
        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.wait_for(task_fn(), timeout=timeout_seconds)
                results[index] = result
                return
            except asyncio.TimeoutError:
                print(f"Task {index} timed out on attempt {attempt + 1}")
            except Exception as e:
                print(f"Task {index} failed with error: {e}")
                return
        print(f"Task {index} failed after {max_retries + 1} attempts")

    async with anyio.create_task_group() as tg:
        for i, task_fn in enumerate(tasks):
            tg.start_soon(_run_task, task_fn, i)

    return results


def split_into_units(content) -> list[str]:
    """
    Split content into units based on headings with numbers (e.g., 1.1, 1.2, 2.1)
    """
    import re

    # Pattern to match headings with unit numbers (e.g., ### 1.1, ## 2.3, # 1.1)
    unit_pattern = r'^(#{1,6})\s+(\d+\.\d+)\s+(.+)$'

    lines = content.split('\n')
    units = []
    current_unit = None

    for line in lines:
        # check if this line is a unit heading
        match = re.match(unit_pattern, line, re.MULTILINE)

        if match:
            # save previous unit if exists
            if current_unit:
                units.append(current_unit)
            line = line.replace("#","")
            current_unit = f"Unit Title: {line} + '\n'"
        else:
            # Add line to the current unit
            if current_unit:
                current_unit += line + '\n'
            elif line.strip():  # Only add non-empty lines
                if units:
                    units[-1] += line + '\n'

    if current_unit:
        units.append(current_unit)

    return units

import openai

def get_embedding(text: str) -> list[float]:
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
