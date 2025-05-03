# microsoft_hackathon

# 📦 B2B Logistics Intelligence Pipeline (Pathway + RAG)

## 🧾 Overview

This project simulates a real-world B2B logistics pipeline for tracking product deliveries, shipping events, and customer orders. It integrates real-time data streaming using **Pathway**, document reasoning using **RAG (Retrieval-Augmented Generation)**, and natural language answering using **OpenAI GPT models**.

---

## 📁 Datasets

### 1. `Table1_Products.csv`
Contains product catalog information:
- `product_id` (PK): Unique ID for each product
- `category`, `subcategory`: Product classification
- `list_price`, `discount`, `final_price`
- `supplier_count`, `suppliers`
- `availability`: Stock status
- `eta`: Estimated time of arrival

### 2. `Table2_Shipping.csv`
Tracks shipment status for each product:
- `shipment_id` (PK): Unique shipment record
- `product_id` (FK): References Table1
- `carrier`, `origin`, `destination`
- `status`: Live shipping state (e.g., Delivered, Exception)
- `last_update`: Timestamp of last change

### 3. `Table3_Orders.csv`
Logs customer orders:
- `order_id` (PK): Unique order
- `customer_name`, `order_time`, `delivery_location`
- `product_id` (FK): References Table1
- `quantity`, `payment_method`

---

## 🧠 Company Policy Document
- `Company_Policy_Logistics.pdf`: Contains rule-based clauses related to delivery timelines, returns, shipping exceptions, and supplier evaluation. This document is indexed for retrieval in the RAG system.

---

## ⚙️ Project Pipeline

1. **Data Generation**
   - Simulated using Python (`faker`, `pandas`)
   - Exported to CSV files for Pathway ingestion

2. **Real-Time Streaming with Pathway**
   - Watches datasets (e.g., shipping logs) for new entries
   - Feeds updates into a real-time processing flow

3. **RAG Integration using Pathway**
   - Embeds policy + shipment text using `SentenceTransformers`
   - Stores embeddings in a FAISS index
   - Retrieves context based on user queries

4. **Answer Generation**
   - Uses `OpenAI GPT` to respond to questions like:
     - “Which shipment is delayed?”
     - “What’s the penalty clause for late delivery?”
     - “Which supplier had a damaged shipment?”

---

## ✅ Deliverables

- 📁 CSV Datasets:
  - `Table1_Products.csv`
  - `Table2_Shipping.csv`
  - `Table3_Orders.csv`
- 📄 Company Policy:
  - `Company_Policy_Logistics.pdf`
- 🧠 RAG Pipeline Scripts:
  - `main.py` (Pathway streaming)
  - `retriever.py` (RAG search + GPT response)
- 📜 README (this file)

---

## 🔍 Example Queries

- "What is the ETA for product PDT015?"
- "Was there any damage report in the last 48 hours?"
- "Which clause applies if the shipment is marked Exception?"

---

## 🧑‍💻 Frameworks & Tools Used

- `pathway` – real-time data streaming
- `pandas`, `faker` – synthetic dataset generation
- `sentence-transformers`, `faiss` – document embedding + retrieval
- `openai` – LLM answer generation
- `fpdf` – PDF generation for policy docs

---

## 🚀 Final Output
A working prototype of a B2B logistics assistant capable of:
- Live querying of shipment/order/product data
- Answering rule-based questions via company policy
- Scaling to additional rules, live ETL, and UI integration

