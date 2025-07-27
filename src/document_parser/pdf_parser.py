from llama_parse import LlamaParse
import nest_asyncio
import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from io import BytesIO
import base64

load_dotenv()
nest_asyncio.apply()

ins = """
You are a highly proficient language model designed to convert pages from PDF, PPT, and other files into structured markdown text. Your goal is to accurately transcribe text, and identify and describe images, particularly graphs and other graphical elements.

### Reading Order Instruction:

* Maintain the correct **visual sequence** of all elements based on this reading order.
Important: Please put the figure label/caption at the correct section container based on semantic meaning.

- Please add page number indicated in the pdf page at the end of each md text as format: page_number: {{page_number}}
- Please ignore the header of the pdf to keep the continuous information flow between pages.
- Please distinguish the hierarchical heading: with chapter: use #, with units use ##, with section (green big text) use ###, with subsection use ####. Do not create subsubsection.

### For the following elements, follow these extraction rules:

#### Text:
* Extract **all readable text** from the pages.
* **Preserve the visual grouping** and natural flow of headings, subheadings, and paragraphs.
"""


class PDFParser(object):
    def __init__(self, parsing_ins):
        self.parser = LlamaParse(
            verbose=True,
            do_not_cache=True,
            user_prompt=parsing_ins,
            premium_mode=True
        )

    def get_image_nodes(self,file_path: str, image_format='png'):
        """Extract out text from images using a multimodal model."""
         # self.parser.get_images(json_objs, download_path=download_path)
        # img_text_nodes = []
        # for image_dict in image_dicts:
        #     image_doc = ImageDocument(image_path=image_dict["path"])
        #     img_text_nodes.append(image_doc)

        pages = convert_from_path(file_path, dpi=300)
        image_dicts = {}

        for idx, page in enumerate(pages, start=1):
            buffered = BytesIO()
            page.save(buffered, format=image_format)
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            ext = image_format.lower()
            image_dicts[idx] = {
                "base64": img_str,
                "ext": ext,
                "data_uri": f"data:image/{ext};base64,{img_str}"
            }

        return image_dicts

    def document_processing_llamaparse(self, file_path: str):
        """Parse document in using llamaparse and return extracted elements in json format"""
        json_objs = self.parser.get_json_result(file_path)
        json_list = json_objs[0]["pages"]

        image_dicts = self.get_image_nodes(file_path)

        return json_list, image_dicts


llama_parser = PDFParser(parsing_ins=ins)
# llamaparse to extract documents
json_list, image_dicts = llama_parser.document_processing_llamaparse(
    file_path="Cells and Chemistry of Life.pdf")
