import os
import json
from dotenv import load_dotenv
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

# ===== Load Env Config =====
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# ===== Paths =====
SHIPPING_DOCS_PATH = "output/shipping_docs.jsonl"
POLICY_TEXT_PATH = "policy_clauses.txt"

# ===== Load Data =====
def load_documents():
    docs = []

    # Load shipping data
    with open(SHIPPING_DOCS_PATH) as f:
        for line in f:
            data = json.loads(line)
            docs.append(Document(page_content=data["text"], metadata={"shipment_id": data["shipment_id"]}))

    # Load policy data
    with open(POLICY_TEXT_PATH) as f:
        policy_clauses = f.read().split("\n\n")
        docs += [Document(page_content=clause.strip(), metadata={"source": "policy"}) for clause in policy_clauses if clause.strip()]

    return docs

# ===== Initialize Vector Store =====
def create_vector_store(docs):
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(docs, embeddings)

# ===== Build Prompt & Chain =====
def build_qa_chain(vectorstore):
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a smart logistics assistant. Use the context to answer the question precisely.

Context:
{context}

Answer the logistics-related question:
{question}
Answer:"""
    )

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

# ===== Ask a Question =====
def ask_question(qa_chain, question):
    result = qa_chain.invoke({"query": question})
    print("\n🔎 Answer:", result["result"])

    # Save sources
    sources = [doc.page_content for doc in result["source_documents"]]
    keyword = "".join(e for e in question if e.isalnum())[:50]
    file_path = f"output/answer_sources_{keyword}.csv"
    Path("output").mkdir(exist_ok=True)
    with open(file_path, "w") as f:
        for s in sources:
            f.write(s + "\n---\n")

    print(f"📁 Saved source docs to: {file_path}")

# ===== Run RAG Assistant =====
if __name__ == "__main__":
    print("🚀 Initializing RAG-based Logistics Assistant...")
    documents = load_documents()
    vectorstore = create_vector_store(documents)
    qa_chain = build_qa_chain(vectorstore)

    print("✅ Ready! Ask logistics-related questions. Type 'exit' to quit.")
    while True:
        q = input("\n❓ Your question: ")
        if q.lower() == "exit":
            break
        ask_question(qa_chain, q)
