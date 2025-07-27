# gradio_app.py
import gradio as gr
import nest_asyncio
nest_asyncio.apply()
from src.query import query

def qa_pipeline(user_input):
    import asyncio
    answer, _ = asyncio.run(query(user_input))
    return answer

demo = gr.Interface(
    fn=qa_pipeline,
    inputs=gr.Textbox(lines=3, label="Ask a question"),
    outputs=gr.Textbox(label="Answer"),
    title="Knowledge Base Q&A Chatbot"
)

demo.launch()