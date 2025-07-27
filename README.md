* ****## Multi-modal Agentic RAG Report
* 
* ### I. RAG Implementation
* 
* To build a Retrieval-Augmented Generation (RAG) chatbot for the provided knowledge base (KB), the following approach was adopted:
* 
* #### 1. Knowledge Base Loading
* 
* ##### 1.1 PDF Parsing
* 
* - **Technology Used:** [LlamaParse](https://www.llamaindex.ai/llamaparse)
* - **Reasoning:**  
*   - I experimented with various libraries such as `pymupdf` and `pypdf` for PDF content extraction. Ultimately, LlamaParse offered the best parsing performance.
*   - LlamaParse converts documents into markdown format, which has been shown to improve RAG efficiency in several studies.
*   - The parser effectively captures table and figure captions and organizes them within the relevant sections.
* 
* - **Known Issues:**  
*   - The images extracted from the PDF are sometimes split into fragments. I attempted to use bounding boxes to capture complete figures, but this approach was unsuccessful.
* 
* - **Workaround:**  
*   - I discovered that passing the full page image (containing the figure) to a Vision Language Model allows for effective figure interpretation. As a result, the KB stores information about each figure, including its label, caption, and page number.
* 
* ##### 1.2 Ontology Design
* 
* - **Document Structure:**  
*   - The knowledge base follows a hierarchical structure aligned with the original document’s organization.
* 
* - **Rationale:**  
*   - Since the source document is academic, well-structured, and complex (with tables and figures embedded in sections), preserving its hierarchy (units, sections, etc.) is important for providing rich and relevant context.
*   - Instead of applying simple linear chunking, I utilized logic and LLM-powered parsing to convert the document into structured objects for precise retrieval.
* 
* ![Screenshot](https://ibb.co/F48p3tFw)****
* 
* 