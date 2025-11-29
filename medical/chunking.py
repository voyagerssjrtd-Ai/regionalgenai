from langchain_core.prompts import ChatPromptTemplate
from loader import load_txts
from azure_llm import getMassGpt
from embedding import getLargeEmbedding
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

llm = getMassGpt()
embedding_model = getLargeEmbedding()

def getRetriever():
    txt_documents = load_txts()
    chunked_docs = []
    for doc in txt_documents:
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
                "You are a helpful assistant that splits medical or disease-related documents "
                "into semantically meaningful chunks for downstream semantic search and retrieval."
            ),
            ("human", 
                """You will be given a document. Split it into semantically coherent sections, following these rules:

                1. Do not omit any information.
                2. Keep related items together.
                3. Each chunk should be self-contained.
                4. Aim for ~5000–6000 words per chunk.
                5. Return chunks as a numbered list with headings like '### Chunk 1:', '### Chunk 2:'.
                6. Include metadata (e.g., source) at the beginning of each chunk.

                Document:
                {document}
                """
            )
        ])

        formatted_prompt = prompt.format_messages(document=doc.page_content)
        response = llm.invoke(formatted_prompt)

        chunks = [c.strip() for c in response.content.split("### Chunk") if c.strip()]
        for idx, chunk in enumerate(chunks):
            chunked_docs.append(
                Document(
                    page_content=chunk,
                    metadata={"source": f"{doc.metadata['source']}_chunk{idx+1}"}
                )
            )

    vector_store = Chroma.from_documents(
        chunked_docs,
        embedding_model,
        persist_directory="chroma_db"
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    return retriever