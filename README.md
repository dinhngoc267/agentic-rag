# Multi-modal Agentic RAG Report

This report presents a Retrieval-Augmented Generation (RAG) chatbot pipeline built upon a structured knowledge base (KB) extracted from academic documents. The system integrates multi-modal capabilities and adapts responses for student-friendly engagement.

---

## I. RAG Implementation

### 1. Knowledge Base Loading

#### 1.1 PDF Parsing

- **Technology Used:** [LlamaParse](https://www.llamaindex.ai/llamaparse)  
  - I experimented with several PDF extraction tools, including `pymupdf` and `pypdf`, but LlamaParse delivered the most reliable results.  
  - LlamaParse outputs content in Markdown format, which is beneficial for downstream RAG performance.  
  - The parser also retains structure, tables, and figure captions within their respective sections.

- **Known Issues:**  
  - Extracted images are often split into fragments. I did try to use bounding boxes to reassemble full figures but were unsuccessful.  

- **Workaround:**  
  - I found that sending the entire page image (containing the fragmented figure) to a Vision-Language Model allows for accurate interpretation.  
  - The KB stores metadata for each figure, including label, caption, and page number.

You can find the markdown data here: https://github.com/dinhngoc267/agentic-rag/blob/master/data/document_pages.json

#### 1.2 Ontology Design

- **Document Structure:**  
  - The KB follows a hierarchical structure aligned with the source document.  
  - Each Unit contains multiple Sections. Each Section contains:
    - Figures
    - Tables
    - Mentions (text spans referring to real-world concepts)

- **Rationale:**  
  - The academic source material is complex and structured. Preserving its hierarchy (Units → Sections) allows for more relevant and accurate context retrieval.  
  - Rather than simple linear chunking, the pipeline uses logic and LLM-assisted parsing to build structured objects optimized for retrieval.

- **Result:**

  ![Ontology Result](https://github.com/user-attachments/assets/e821ea1c-6055-46b9-a354-57face5b58d4)

- **Note:**  
  - Extracting mentions and modeling relationships between them can significantly improve retrieval performance in:
    + Domains with high concept ambiguity.
    + Academic text books, where some concepts from different units can be related to each other (often fail in normal chunking technique)
        
  - In this work, only **mention extraction** is implemented; **relation extraction** is left for future work.

#### 1.3 Node Embedding

- Node texts are embedded using OpenAI’s `text-embedding-3-small` model.

#### 1.4 Explore the Knowledge Base

- The constructed KB is available at:  
  https://2eb48c93.databases.neo4j.io/browser/  
  - **Username:** neo4j  
  - **Password:** XIyofUDvcYuAKtvEcU5JOXYM8frrDTT4vbr3pfwYR3c

---

### 2. Agentic RAG

- This system uses **embedding-based retrieval** with a **fixed semantic query**, ensuring that the retrieved context nodes are at the Section level.
- To support **multi-modal question answering**, I developed an **Agentic Multi-modal RAG** workflow. The architecture is illustrated below:

![Agentic RAG Diagram](https://github.com/user-attachments/assets/9f1dba0b-aa60-40e0-81f4-5763ddfe22f1)
- 
- The VLM/LLM can return 3 type of object:
  - `FinalAnswer` contains the final answer to user query
  - `OutOfScope` contains a fixed message (“I'm not sure how to answer that based on the information I have.”) will be used when cannot answer the user query based on given context. 
  - `RequireFigure` contains relevant figures which the query will be better resolved with. 
---

## II. Tone Adaptation and Student Engagement

- The LLM is prompted to generate answers in a tone appropriate for students.  
- Additionally, the LLM can reference the source of its answers (e.g., Unit or Section titles), allowing students to verify information on their own.

---

## III. RAGAS Evaluation

- I used the [RAGAS](https://github.com/explodinggradients/ragas) framework to evaluate the chatbot.  
- A test set of 21 questions  was used to assess:
  - Faithfulness
  - Answer relevancy
  - Context precision
  - Context recall


- Evaluation script is provided in `evaluation.ipynb`.
- You can find the evaluation data (include response and retrieved context of the system) here: https://github.com/dinhngoc267/agentic-rag/blob/master/data/evaluation_data.csv
- **Results:**

  ```
  {
    "context_precision": 1.0000,
    "faithfulness": 0.9135,
    "answer_relevancy": 0.9166,
    "context_recall": 0.9881
  }
  ```

---

#### Video demo:

With text-only answer generation:
https://drive.google.com/file/d/1v2McpifMkOrsrHi38SVhR-dfPSelNAWv/view?usp=sharing

With reqired figure query

https://drive.google.com/file/d/15AtPWjhDhX3YknKQ0tBOxXXOvIkWHmFe/view?usp=sharing 
