from src.kb_construction.kb_loader import Neo4jKBLoader
import os
from dotenv import load_dotenv

from src.kb_construction.utils import get_embedding
from src.kb_retrieval.embedding_based_retriever import KBRetrieval
from src.answer_generation.response_agent import generate_response, FinalAnswer, RequireFigureResponse, OutOfScope

load_dotenv()

def get_figures_by_labels(loader, figure_labels: str):

    # figure_query_embedding = get_embedding(figure_query)

    query = f"""
    MATCH (node:FigureRef)
    WHERE node.label IN {figure_labels}
    RETURN node.label AS label, node.caption AS caption, node.page_number AS page_number
    
    """
    with loader.driver.session() as session:
        result = session.run(
            query,
        )
        return [
            {
                "label": record["label"],
                "caption": record["caption"],
                "page_number": record["page_number"],
            }
            for record in result
        ]



def get_page_images_by_numbers(loader, page_numbers):
    query = f'''
    MATCH (p:PageImage)
    WHERE p.page_number IN {page_numbers}
    RETURN p.page_number AS page_number, p.url AS url
    '''
    with loader.driver.session() as session:
        result = session.run(query, {"page_numbers": page_numbers})
        return {record["page_number"]: record["url"] for record in result}


import requests
from PIL import Image
from io import BytesIO
import base64

def load_image_from_url(url: str) -> Image.Image:
    """
    Downloads an image from a web URL and returns a PIL Image object.
    """
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))

def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    Converts a PIL Image object to a base64 encoded string.
    """
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_b64



def get_images_for_figures(loader, figure_query):
    figures = get_figures_by_labels(loader, figure_query)
    if not figures:
        return {}

    page_numbers = list({fig['page_number'] for fig in figures})  # Unique
    page_images = get_page_images_by_numbers(loader, page_numbers)

    images_info = []
    for page_number, url in page_images.items():
    # for fig in figures:
    #     url = page_images.get(fig['page_number'])
        if url:
            image = load_image_from_url(url)
            image_b64 = image_to_base64(image)
            images_info.append({
                # 'figure_label': fig['label'],
                # 'caption': fig.get('caption', ''),
                # 'page_number': fig['page_number'],
                'image': image_b64
            })
    return images_info


async def query(query: str):
    loader = Neo4jKBLoader(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

    kb_retrieval = KBRetrieval(loader)

    query_embedding = get_embedding(query)

    output = kb_retrieval.query_sections_by_embedding(query_embedding=query_embedding, top_k=15)[:10]

    def build_context(list_node_dict: list):
        context = ""
        for node in list_node_dict:
            if 'unit_title' in node:
                context += f"Unit Title: {node['unit_title']}\n"
            if 'section_title' in node:
                context += f"Section Title: {node['section_title']}\n"

            if "content" in node:
                context += f"Content: {node['content']}\n"
            elif "summary" in node:
                context += f"Summary: {node['summary']}\n"
            context += "\n================\n"

        return context

    context = build_context(output)

    # print(context)


    response = await generate_response(context, query)

    if isinstance(response, FinalAnswer):
        return response.answer, context
    elif isinstance(response, OutOfScope):
        return response.message, context
    elif isinstance(response, RequireFigureResponse):
        figures_labels = response.figures_labels
        images_info = get_images_for_figures(loader, figures_labels)

        messages = []

        # Add context and user query as text
        if context:
            messages.append(
                {"role": "system", "content": "Answer user query based on the given context and the figures mentioned in the user query. Answer the question straightforward. The language you use must be: - Simple and clear - Friendly and suitable for young learners - Encouraging curiosity and understanding. Also if you use the figures information in the images, please note reference (figure label) also."}
            )
        messages.append(
            {"role": "user", "content": f"Context: {context}\nUser Query: {query}"}
        )

        for img in images_info:
            # content = f"{img['figure_label']}: {img['caption']}" if img['caption'] else img['figure_label']
            messages.append(
                {
                    "role": "user",
                    "content": [
                        # {"type": "text", "text": content},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img['image']}"}}
                    ]
                }
            )
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
        )
        response = response.choices[0].message.content

    return response, context

if __name__ == "__main__":
    import asyncio
    res = asyncio.run(query(
        """
Figure 1.26 shows a typical plant cell. Which of the numbered structures are partially permeable?        """
    ))

    print(res)
    #
    # import pandas as pd
    #
    # df = pd.read_csv("/home/ju/PycharmProjects/heyhi/data/testset.csv")
    #
    # queries = df['user_input'].to_list()
    #
    # res_buffer = []
    # context_buffer = []
    # for query_string in queries:
    #     print(query_string)
    #     print("=====================")
    #     res, context = asyncio.run(query(query_string))
    #     print(res)
    #     res_buffer.append(res)
    #     context_buffer.append(context)
    #     print("=====================")
    #
    # df['answer'] = res_buffer
    # df['contexts'] = context_buffer
    # df.to_csv("/home/ju/PycharmProjects/heyhi/data/test_data_with_answer.csv", index=False)
