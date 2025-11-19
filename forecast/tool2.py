import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------
# INIT MCP SERVER
# ---------------------------------------------
mcp = FastMCP("PDFQuery")

# ---------------------------------------------
# LOAD ENV + MODELS
# ---------------------------------------------
load_dotenv()

embedding_model = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4", temperature=0.2)

# ---------------------------------------------
# LOAD & CHUNK PDF → VECTOR DB
# ---------------------------------------------
def loading_and_chunking():
    loader = PyPDFLoader(r"c:\Users\Genaiblrpiousr13\Downloads\test\checking\files\photos.pdf")
    docs = loader.load()
    full_text = "\n".join([doc.page_content for doc in docs])

    chunk_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that chunks documents for semantic search."),
        ("human", "Split the following document into semantically meaningful sections. Return each chunk as a numbered list.\n\n{document}")
    ])

    formatted_prompt = chunk_prompt.format_messages(document=full_text)
    response = llm.invoke(formatted_prompt)
    chunks = response.content.split("\n\n")

    chunked_docs = [Document(page_content=chunk.strip()) for chunk in chunks if chunk.strip()]

    vector_store = Chroma.from_documents(
        chunked_docs,
        embedding_model,
        persist_directory="chroma_pdf_db"
    )
    vector_store.persist()
    return vector_store.as_retriever(search_kwargs={"k": 3})

retriever = loading_and_chunking()

# ---------------------------------------------
# MCP TOOL: Query PDF
# ---------------------------------------------
@mcp.tool()
def query_pdf(question: str) -> str:
    """Answer questions based on the PDF content using semantic search."""
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers questions based on retrieved documents."),
        ("human", "Answer the question using the following context:\n\n{context}\n\nQuestion: {question}")
    ])

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | qa_prompt
        | llm
    )
    response = rag_chain.invoke(question)
    return response.content

# ---------------------------------------------
# MCP ENTRY POINT
# ---------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")