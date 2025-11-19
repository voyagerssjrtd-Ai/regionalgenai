import os
import re
import pandas as pd
from dotenv import load_dotenv

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------
# INIT MCP SERVER
# ---------------------------------------------
mcp = FastMCP("DairySales")

# ---------------------------------------------
# LOAD ENV + MODELS
# ---------------------------------------------
load_dotenv()

embedding_model = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4", temperature=0.2)

# ---------------------------------------------
# LOAD DATA
# ---------------------------------------------
df = pd.read_csv(r"c:\Users\genaiblrancusr103\Desktop\TEST\csvfiles\Dairy_Historical_Sales.csv")
df["Year"] = df["Month"].str[:4]
df["MonthNum"] = df["Month"].str[5:7]

# ---------------------------------------------
# CREATE YEAR-CHUNKED DOCUMENTS
# ---------------------------------------------
chunked_docs = []

for year, group in df.groupby("Year"):
    text = f"YEAR: {year}\n" + group.to_string(index=False)
    chunked_docs.append(Document(page_content=text, metadata={"year": year}))

# ---------------------------------------------
# CREATE VECTOR DB
# ---------------------------------------------
vectordb = Chroma.from_documents(
    documents=chunked_docs,
    embedding=embedding_model,
    persist_directory="chroma_db_fixed"
)
vectordb.persist()

# ---------------------------------------------
# FILTER EXTRACTION
# ---------------------------------------------
def extract_filters(question: str):
    year = None
    month = None

    y = re.search(r"\b(20\d{2})\b", question)
    if y:
        year = y.group(1)

    months = {
        "jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
        "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"
    }

    q = question.lower()
    for mname, mnum in months.items():
        if re.search(rf"\b{mname}\b", q):
            month = mnum

    return year, month

# ---------------------------------------------
# MCP TOOL: Ask Dairy Sales Question
# ---------------------------------------------
@mcp.tool()
def ask_dairy_sales(question: str) -> str:
    """Answer dairy sales questions using historical CSV and vector search."""
    year, month = extract_filters(question)

    if year and not month:
        docs = vectordb.similarity_search(query=question, k=1, filter={"year": year})
        if docs:
            context = docs[0].page_content
        else:
            context = "No data found for this year."
        
    elif year and month:
        row = df[(df["Year"] == year) & (df["MonthNum"] == month)]
        if not row.empty:
            context = row.to_string(index=False)
        else:
            context = "No matching year-month found."

    else:
        docs = vectordb.similarity_search(question, k=2)
        context = "\n\n".join([d.page_content for d in docs])

    prompt = f"""
    Use ONLY the DATA shown below to answer the question.
    Do NOT hallucinate missing values.

    DATA:
    ```
    {context}
    ```

    QUESTION:
    {question}
    """

    response = llm.invoke(prompt)
    return response.content

# ---------------------------------------------
# MCP ENTRY POINT
# ---------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")