import os
import pandas as pd
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import DataFrameLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from apscheduler.schedulers.background import BackgroundScheduler

# ====== Load Config ======
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# ====== Globals ======
qa_chain = None
vectorstore = None
docs = []
combined_df = pd.DataFrame()

# ====== Helper: Clean keyword for filename ======
def slugify(text):
    return re.sub(r'[^a-zA-Z0-9]+', '_', text.strip().lower())[:60].strip('_')

# ====== Reload Pathway Output → Refresh Vector Store ======
def reload_data_from_pathway():
    global qa_chain, vectorstore, docs, combined_df

    # Read Pathway's JSONL output
    shipping_docs = pd.read_json("output/shipping_docs.jsonl", lines=True)

    # Split into DataFrames (customize based on your JSONL structure)
    order_data = shipping_docs[["order_id", "customer", "quantity"]]
    product_catalog = shipping_docs[["product_id", "product_name", "category", "price"]]
    shipping_logistics = shipping_docs[["shipment_id", "carrier", "destination", "status"]]

    # Generate text fields
    order_data['text'] = order_data.apply(
        lambda row: f"Order ID: {row.order_id} | Customer: {row.customer} | Quantity: {row.quantity}",
        axis=1
    )

    product_catalog['text'] = product_catalog.apply(
        lambda row: f"Product ID: {row.product_id} | Name: {row.product_name} | Category: {row.category}",
        axis=1
    )

    shipping_logistics['text'] = shipping_logistics.apply(
        lambda row: f"Shipment ID: {row.shipment_id} | Carrier: {row.carrier} | Destination: {row.destination}",
        axis=1
    )

    # Combine for vector store
    combined_df = pd.concat([
        order_data[['text']],
        product_catalog[['text']],
        shipping_logistics[['text']]
    ])

    # Rest of your existing processing code remains unchanged...
    loader = DataFrameLoader(combined_df, page_content_column="text")
    docs = loader.load()

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="... your existing template ..."
    )

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 8}),
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=True
    )

# ====== Update Scheduler ======
def start_polling():
    scheduler = BackgroundScheduler()
    scheduler.add_job(reload_data_from_pathway, "interval", seconds=60)
    scheduler.start()

# ====== Run Server ======
if __name__ == "__main__":
    reload_data_from_pathway()  # Changed from reload_data_from_mongodb
    start_polling()
    print("✅ Logistics AI Ready (Using Pathway Data)")
    while True:
        question = input("\n❓ Your question: ")
        if question.lower() == "exit":
            break
        answer_question(question)
