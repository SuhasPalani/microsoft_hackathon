import os
import pandas as pd
import re
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_community.document_loaders import DataFrameLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from apscheduler.schedulers.background import BackgroundScheduler

# ====== Load Config ======
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client['ecommerce']

# ====== Globals ======
qa_chain = None
vectorstore = None
docs = []
combined_df = pd.DataFrame()


# ====== Helper: Clean keyword for filename ======
def slugify(text):
    return re.sub(r'[^a-zA-Z0-9]+', '_', text.strip().lower())[:60].strip('_')


# ====== Reload MongoDB → Refresh Vector Store → Silent Save ======
def reload_data_from_mongodb():
    global qa_chain, vectorstore, docs, combined_df

    order_data = pd.DataFrame(list(db.orders.find()))
    product_catalog = pd.DataFrame(list(db.products.find()))
    shipping_logistics = pd.DataFrame(list(db.shipping.find()))

    for df in [order_data, product_catalog, shipping_logistics]:
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

    order_data['text'] = order_data.apply(
        lambda row: f"Order Placement: {row.get('order_placement', '')}, "
                    f"Customer: {row.get('customer_name', '')}, "
                    f"Time of Order: {row.get('time_of_order', '')}, "
                    f"Location: {row.get('location', '')}, "
                    f"Product ID: {row.get('product_id', '')}, "
                    f"Quantity: {row.get('quantity', '')}, "
                    f"Payment Method: {row.get('payment_method', '')}",
        axis=1
    )

    product_catalog['text'] = product_catalog.apply(
        lambda row: f"Product ID: {row.get('product_id', '')}, "
                    f"Category: {row.get('product_category', '')}, "
                    f"Subcategory: {row.get('product_subcategory', '')}, "
                    f"Price: ${row.get('price', '')}, "
                    f"List Price: ${row.get('listprice', '')}, "
                    f"Discount Price: ${row.get('discountprice', '')}, "
                    f"Supplier: {row.get('supplier', '')}, "
                    f"Availability: {row.get('product_availability', '')}, "
                    f"ETA: {row.get('eta', '')}",
        axis=1
    )

    shipping_logistics['text'] = shipping_logistics.apply(
        lambda row: f"Order Placement: {row.get('order_placement', '')}, "
                    f"Customer: {row.get('customer_name', '')}, "
                    f"Time of Order: {row.get('time_of_order', '')}, "
                    f"Location: {row.get('location', '')}, "
                    f"Product ID: {row.get('product_id', '')}, "
                    f"Category: {row.get('product_category', '')}, "
                    f"Subcategory: {row.get('product_subcategory', '')}, "
                    f"Quantity: {row.get('quantity', '')}, "
                    f"Payment Method: {row.get('payment_method', '')}, "
                    f"Price: ${row.get('price', '')}, "
                    f"Supplier: {row.get('supplier', '')}, "
                    f"Carrier: {row.get('carrier', '')}, "
                    f"Tracking Number: {row.get('tracking_number', '')}, "
                    f"Shipment Date: {row.get('shipment_date', '')}, "
                    f"Estimated Delivery: {row.get('estimated_delivery', '')}, "
                    f"Actual Delivery: {row.get('actual_delivery', 'Not delivered yet')}, "
                    f"Status: {row.get('status', '')}",
        axis=1
    )

    # Combine for vector store
    combined_df = pd.concat([
        order_data[['text']],
        product_catalog[['text']],
        shipping_logistics[['text']]
    ])

    loader = DataFrameLoader(combined_df, page_content_column="text")
    docs = loader.load()

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)

    # Create Retrieval Chain
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a helpful logistics assistant with access to shipping, order, and product information.
Use the following context to answer the question. If you don't know the answer, say so.

Context:
{context}

The data includes:
- Order information: order placement time, customer name, product ID, quantity, payment method
- Product information: product ID, category, subcategory, price, availability
- Shipping information: carrier, tracking number, shipment date, estimated delivery, actual delivery, status

Question: {question}
Answer:"""
    )

    llm = ChatOpenAI(model="gpt-4", temperature=0)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 8}),
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=True
    )

    # Silently save full index snapshot (optional for debugging)
    combined_df.to_csv("vector_index_snapshot.csv", index=False)


# ====== Handle Question: Answer + Save Relevant Docs ======
def answer_question(question):
    global qa_chain
    try:
        result = qa_chain.invoke({"query": question})
        print("\n🔎 Answer:", result["result"])

        # Save only relevant source docs
        keyword = slugify(question)
        filename = f"search_output_{keyword}.csv"
        source_texts = [doc.page_content for doc in result["source_documents"]]
        pd.DataFrame(source_texts, columns=["text"]).to_csv(filename, index=False)
        print(f"📁 Relevant source data saved to: {filename}")

    except Exception as e:
        print(f"❌ Error: {e}")


# ====== Scheduler to Refresh Every 30s ======
def start_polling():
    scheduler = BackgroundScheduler()
    scheduler.add_job(reload_data_from_mongodb, "interval", seconds=60)
    scheduler.start()


# ====== Run Server ======
if __name__ == "__main__":
    reload_data_from_mongodb()
    start_polling()

    print("✅ Logistics AI Ready — Ask your questions below (type 'exit' to quit)")
    while True:
        question = input("\n❓ Your question: ")
        if question.lower() == "exit":
            break
        answer_question(question)
