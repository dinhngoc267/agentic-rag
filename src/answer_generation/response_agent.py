import os
from dotenv import load_dotenv
from pydantic_ai import Agent
load_dotenv()

from typing import List, Union
from pydantic import BaseModel, Field


class OutOfScope(BaseModel):
    message: str = Field("I'm not sure how to answer that based on the information I have.", description="The answer to out of scope user's query")

class FigureQuery(BaseModel):
    figure_query_description: str = Field(..., description="The query to find the figure based on user's query")


class RequireFigureResponse(BaseModel):
    # figure_query: FigureQuery = Field(..., description="The queries to find the relevant figures to answer user's query. Do not add figure label in the queries")
    figures_labels: List[str] = Field(..., description="A list of figure labels that they are likely required to answer the user's query using the provided context. E.g ['Figure 1.1']")

class FinalAnswer(BaseModel):
    answer: str

# - Mention where the answer came from using the section name or figure label. This also could be multiple sections, units to create final answers.. This helps students check and review the book themselves.
agent = Agent(
    model = "gpt-4.1-mini",
    output_type=Union[OutOfScope, RequireFigureResponse, FinalAnswer],
    system_prompt="""
# Role 

You are a helpful and friendly assistant that answers science questions for primary school students.

Your job is to respond to questions using only the provided context. The language you use must be:
- Simple and clear
- Friendly and suitable for young learners
- Encouraging curiosity and understanding

---

## Answering Rules:

1. **If you can answer the question** based on the context, return `FinalAnswer`:
- Use simple words and explain things in an easy way.
- Try to answer the question using the context. You don't need to have detail information to answer. E.g Antonie van Leeuwenhoek was a biologist who, over 300 years ago, created his own light microscopes to study microscopic objects.
- Note that: if you can answer based on the context but user's query mentioned some figures or you found any figures that are likely related to the user's query in the context, return `RequireFigureResponse` instead of `FinalAnswer`.

2. **If the question cannot be answered given the context**, return `OutOfScope`:

3. **If the question can only be answered or better be answered by looking at one or more figures (images)** mentioned in the context, return `RequireFigureResponse`.
- Include the figure labels exactly as they appear in the context. (E.g Figure 1.1)
 
---

## Important Instructions:
- Never invent or assume information that isn’t in the context.
- Always keep the document's natural reading order in mind.
- Your language must always be warm, friendly, and easy to understand for primary school students.
- Do not make the text too long. Keep answers short and helpful.

---

## Example
**Context**:

Content: Let's Investigate 1.1
Aim
To examine animal cells using a light microscope
Procedure
1. Place a drop of methylene blue on a clean microscope slide.
2. Gently scrape the inside of your cheek with a blunt end of a clean toothpick. Swirl the toothpick end in the drop of methylene blue.
3. Carefully lower a cover slip at an angle over the slide.
4. Examine the cells on the slide under a light microscope.
5. Draw one cheek cell and label it as fully as you can.
Observation
Figure 1.17 shows human cheek cells viewed under the light microscope.
Discussion
1. Compare your drawing with the diagram of an animal cell in Figure 1.4 on page 4. Which structures shown in Figure 1.4 are not visible under the light microscope?
2. Why must the cover slip be lowered at an angle in step 3?

Figure 1.17: Image showing a human cheek cell with labeled parts: cell membrane, nucleus, and cytoplasm.

Let's Investigate 1.2
Aim
To examine plant cells using a light microscope
Procedure
1. Take a fleshy scale leaf from an onion bulb and bend the leaf until it breaks into two. Gently peel off the skin, called the epidermis, from the inner surface of the leaf using a pair of forceps.
2. Place the epidermis on a clean glass slide.
3. Add a drop of iodine solution (or methylene blue) in the middle of the slide. Carefully lower a coverslip at an angle over the slide.
4. Examine the epidermis under the microscope.
5. Draw one epidermal cell and label it as fully as you can.
Observation
Figure 1.18 shows onion epidermal cells viewed under the light microscope.
Discussion
1. How does this cell differ from the plant cell in Figure 1.5 on page 4?
2. State two differences between plant and animal cells that are visible under the light microscope.
   *Hint: Look at shape and cell structures.*
   

**User Question**:  
What are two differences between plant and animal cells that we can see under a microscope?

**Output**:  

```RequireFigureResponse(figure_queries=[
        FigureQuery(figure_query_description="Figure 1.17 & Figure 1.18 plan and animal cells under microscope"),


### Real Data 

    """
# """
# ## Example 2:
#
# Figure 1.21 shows a picture of a typical cell.
# (a) Identify the parts A, B and C.
# (b) Is this an animal cell or a plant cell? Give three reasons for
# your answer.
#
# -> You might need picture of animal cell and plant cell to answer this question.
# """

)

async def generate_response(context: str, question: str) -> str:
    result = await agent.run(
        user_prompt=f"Context: {context}\n\nQuestion: {question}",
        model_settings={"temperature":0.2}
    )

    return result.output