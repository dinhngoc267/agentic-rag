import os
import json
import asyncio
from dotenv import load_dotenv
from doc_distiller import Distiller
from models import Unit
from kb_loader import Neo4jKBLoader
from utils import get_embedding
from src.kb_construction.models import PageImage

load_dotenv()

DOCUMENT_PATH = "document_pages.json"


# ----------------------------------------

def enrich_embeddings(units):
    for unit in units:
        unit.embedding = get_embedding(repr(unit))
        for section in getattr(unit, "sections", []):
            section.embedding = get_embedding(repr(section))
            for mention in getattr(section, "mentions", []):
                mention.embedding = get_embedding(repr(mention))
            for fig in getattr(section, "fig_refs", []):
                fig.embedding = get_embedding(repr(fig))
    return units


def clean_markdown(json_list):
    """Pre-process markdown as in Distiller.main"""
    for idx, item in enumerate(json_list):
        md_lines = [
            line for line in item['md'].split("\n")[:-1]
            if line.strip() != "" and line.count("#") not in [1, 2]
        ]
        json_list[idx]['md'] = (
                f"\npage_number: {str(item['page'])}\n"
                + "\n".join(md_lines)
                + f"\npage_number: {str(item['page'])}"
        )

    return json_list


async def main():
    # 1. Load and clean the document
    with open(DOCUMENT_PATH, "r") as f:
        json_list = json.load(f)
    json_list = clean_markdown(json_list)

    markdown_text = "\n[BREAK_PAGE]\n".join([item['md'] for item in json_list if item['md'] != ""])

    # 2. Distill into units, sections, figures,..
    distiller = Distiller(output_type=Unit)
    units = await distiller.distill(markdown_text)

    # 3. Generate embeddings
    _ = enrich_embeddings(units)

    # 4. Load into Neo4j
    loader = Neo4jKBLoader(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

    for unit in units:
        loader.upsert_node("Unit", unit)
        for section in getattr(unit, "sections", []):
            loader.upsert_node("Section", section)
            loader.upsert_relationship(unit.id, section.id, "HAS_SECTION")
            for mention in getattr(section, "mentions", []):
                loader.upsert_node("Mention", mention)
                loader.upsert_relationship(section.id, mention.id, "HAS_MENTION")
            for fig in getattr(section, "fig_refs", []):
                loader.upsert_node("FigureRef", fig)
                loader.upsert_relationship(section.id, fig.id, "HAS_FIGURE")

    loader.create_vector_index(embedding_dim=1536, similarity_metric="cosine")

    # load images
    with open("image_dict.json", "r") as f:
        image_dicts = json.load(f)

    for page_number, url in image_dicts.items():
        page_image = PageImage(
            page_number=page_number,
            url=url,
        )
        loader.upsert_node("PageImage", page_image)


if __name__ == "__main__":
    asyncio.run(main())
