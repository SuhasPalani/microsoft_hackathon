import os
import time
import random
import pandas as pd
import numpy as np
from faker import Faker
from flask import Flask, jsonify
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# ====== Environment Setup ======
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file!")

# ====== MongoDB & App Setup ======
client = MongoClient(MONGO_URI)
db = client['ecommerce']
app = Flask(__name__)
fake = Faker()

# ====== File Paths ======
PRODUCT_CSV = 'product_catalog.csv'
ORDER_CSV = 'order_data.csv'
SHIPPING_CSV = 'shipping_logistics.csv'

# ====== Load Static Data ======
suppliers = [f"Supplier_{i}" for i in range(1, 11)]
categories = {
    "Electronics": {"code": "ELEC", "subcategories": {"Smartphones": "SM", "Laptops": "LAP", "Tablets": "TAB", "Cameras": "CAM"}},
    "Furniture": {"code": "FURN", "subcategories": {"Desks": "DSK", "Chairs": "CHR", "Beds": "BED", "Cabinets": "CAB"}},
    "Apparel": {"code": "APPR", "subcategories": {"Shirts": "SHT", "Jeans": "JNS", "Shoes": "SHS", "Jackets": "JKT"}},
    "Groceries": {"code": "GROC", "subcategories": {"Snacks": "SNK", "Beverages": "BEV", "Fruits": "FRT", "Vegetables": "VEG"}},
    "Automotive": {"code": "AUTO", "subcategories": {"Tires": "TIR", "Oil": "OIL", "Batteries": "BAT", "Filters": "FIL"}}
}
subcategory_counts = {}

# ====== Faker Product Generator ======
def generate_fake_products(n=5):
    global subcategory_counts
    rows = []
    for _ in range(n):
        category = random.choice(list(categories))
        cat_code = categories[category]["code"]
        subcategory = random.choice(list(categories[category]["subcategories"]))
        subcat_code = categories[category]["subcategories"][subcategory]

        subcategory_counts[subcat_code] = subcategory_counts.get(subcat_code, 0) + 1
        serial = f"{subcategory_counts[subcat_code]:04d}"
        product_id = f"{cat_code}-{subcat_code}-{serial}"

        list_price = round(random.uniform(50, 2000), 2)
        discount = round(random.uniform(0, 0.3), 2)
        discount_price = round(list_price * (1 - discount), 2)
        price = discount_price

        supplier_count = random.choice([1, 2])
        supplier_list = ", ".join(random.sample(suppliers, supplier_count))
        availability = random.choice(["In Stock", "Out of Stock", "Limited"])
        eta = fake.date_between(start_date="+1d", end_date="+15d").strftime("%Y-%m-%d")

        rows.append([
            product_id, category, subcategory, f"${price:,.2f}", f"${list_price:,.2f}", f"${discount_price:,.2f}",
            supplier_list, availability, eta
        ])
    return rows

# ====== Faker Order Generator ======
def generate_fake_orders(product_df, n=5):
    rows = []
    for _ in range(n):
        product = product_df.sample(1).iloc[0]
        city = fake.city()
        state = fake.state()
        country = fake.country()
        pincode = fake.postcode()
        full_location = f"{city}, {state}, {country} - {pincode}"

        rows.append({
            "order_placement": fake.date_time_between(start_date='-30d', end_date='now'),
            "customer_name": fake.name(),
            "time_of_order": fake.time(),
            "location": full_location,
            "product_id": product['product_id'],
            "quantity": random.randint(1, 5),
            "payment_method": random.choice(['Credit Card', 'Debit Card', 'Paypal'])
        })
    return pd.DataFrame(rows)

# ====== Periodic Update Function ======
def update_csv_and_mongo():
    print("🔁 Updating data...")
    # Load existing product catalog
    if os.path.exists(PRODUCT_CSV):
        product_df = pd.read_csv(PRODUCT_CSV)
    else:
        product_df = pd.DataFrame(columns=[
            "product_id", "product_category", "product_subcategory", "price", "listprice", "discountprice",
            "supplier", "product_availability", "eta"
        ])

    # Append new products
    new_products = generate_fake_products(n=5)
    new_df = pd.DataFrame(new_products, columns=product_df.columns)
    product_df = pd.concat([product_df, new_df], ignore_index=True)
    product_df.to_csv(PRODUCT_CSV, index=False)

    # Generate and append new orders
    new_orders = generate_fake_orders(product_df, n=5)
    if os.path.exists(ORDER_CSV):
        order_df = pd.read_csv(ORDER_CSV)
        order_df = pd.concat([order_df, new_orders], ignore_index=True)
    else:
        order_df = new_orders
    order_df.to_csv(ORDER_CSV, index=False)

    # Push to MongoDB
    db.products.delete_many({})
    db.orders.delete_many({})
    db.products.insert_many(product_df.to_dict(orient='records'))
    db.orders.insert_many(order_df.to_dict(orient='records'))

    print("✅ New data appended to CSV")

# ====== Manual Shipping Update ======
def generate_shipping_logistics():
    print("🚚 Generating shipping logistics...")
    orders = pd.read_csv(ORDER_CSV)
    products = pd.read_csv(PRODUCT_CSV)
    shipping = pd.merge(orders, products, on='product_id', how='left')

    # Generate shipping fields
    shipping['shipment_date'] = pd.to_datetime(shipping['order_placement']) + pd.to_timedelta(np.random.randint(0, 3, size=len(shipping)), unit='D')
    shipping['estimated_delivery'] = shipping['shipment_date'] + pd.to_timedelta(np.random.randint(2, 8, size=len(shipping)), unit='D')
    shipping['carrier'] = [fake.company() for _ in range(len(shipping))]
    shipping['tracking_number'] = [fake.bothify(text='???-########') for _ in range(len(shipping))]

    def status_and_actual(row):
        delayed = random.random() < 0.2
        if delayed:
            status = random.choice(["Delayed", "Cancelled"])
            actual = row['estimated_delivery'] + pd.Timedelta(days=random.randint(1, 3)) if status == "Delayed" else ""
        else:
            status = random.choice(["Delivered", "Out for Delivery", "In Transit", "Processing", "Order Received"])
            actual = row['estimated_delivery'] if status == "Delivered" else ""
        return pd.Series([status, actual])

    shipping[['status', 'actual_delivery']] = shipping.apply(status_and_actual, axis=1)

    shipping.to_csv(SHIPPING_CSV, index=False)
    db.shipping.delete_many({})
    db.shipping.insert_many(shipping.to_dict(orient='records'))
    print("✅ Shipping logistics stored in MongoDB")

# ====== Scheduler Start ======
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_csv_and_mongo, 'interval', seconds=60)
    scheduler.start()
    print("📅 Scheduler started (every 60 seconds)")

# ====== Flask Routes ======
@app.route('/')
def home():
    return jsonify({"message": "E-commerce data service is running."})

@app.route('/trigger-shipping-update')
def trigger_shipping():
    generate_shipping_logistics()
    return jsonify({"message": "Manual shipping data generated."})

# ====== Main Entrypoint ======
if __name__ == '__main__':
    update_csv_and_mongo()
    start_scheduler()
    app.run(debug=True, host='0.0.0.0', port=5000)
