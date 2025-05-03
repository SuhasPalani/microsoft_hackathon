# from faker import Faker
# import pandas as pd
# import random
# from collections import defaultdict

# # Initialize Faker
# fake = Faker()

# # Define categories and subcategories with codes
# categories = {
#     "Electronics": {"code": "ELEC", "subcategories": {"Smartphones": "SM", "Laptops": "LAP", "Tablets": "TAB", "Cameras": "CAM"}},
#     "Furniture": {"code": "FURN", "subcategories": {"Desks": "DSK", "Chairs": "CHR", "Beds": "BED", "Cabinets": "CAB"}},
#     "Apparel": {"code": "APPR", "subcategories": {"Shirts": "SHT", "Jeans": "JNS", "Shoes": "SHS", "Jackets": "JKT"}},
#     "Groceries": {"code": "GROC", "subcategories": {"Snacks": "SNK", "Beverages": "BEV", "Fruits": "FRT", "Vegetables": "VEG"}},
#     "Automotive": {"code": "AUTO", "subcategories": {"Tires": "TIR", "Oil": "OIL", "Batteries": "BAT", "Filters": "FIL"}}
# }

# # Sample suppliers
# suppliers = [f"Supplier_{i}" for i in range(1, 11)]

# # Counter to keep track of serial numbers per subcategory
# subcategory_counts = defaultdict(int)

# # Generate product data
# data = []
# for _ in range(150):
#     category = random.choice(list(categories.keys()))
#     cat_code = categories[category]["code"]
#     subcategory = random.choice(list(categories[category]["subcategories"].keys()))
#     subcat_code = categories[category]["subcategories"][subcategory]

#     # Generate product ID
#     subcategory_counts[subcat_code] += 1
#     serial = f"{subcategory_counts[subcat_code]:04d}"
#     product_id = f"{cat_code}-{subcat_code}-{serial}"

#     # Generate pricing info
#     list_price = round(random.uniform(50, 2000), 2)
#     discount = round(random.uniform(0, 0.3), 2)
#     discount_price = round(list_price * (1 - discount), 2)
#     price = discount_price

#     # Format prices as USD strings
#     list_price_str = f"${list_price:,.2f}"
#     discount_price_str = f"${discount_price:,.2f}"
#     price_str = f"${price:,.2f}"

#     # Supplier and availability info
#     supplier_count = random.choice([1, 2])
#     supplier_list = ", ".join(random.sample(suppliers, supplier_count))
#     availability = random.choice(["In Stock", "Out of Stock", "Limited"])
#     eta = fake.date_between(start_date="+1d", end_date="+15d").strftime("%Y-%m-%d")

#     # Append data row
#     data.append([
#         product_id, category, subcategory, price_str, list_price_str, discount_price_str,
#         supplier_list, availability, eta
#     ])

# # Define DataFrame columns
# columns = [
#     "product_id", "product_category", "product_subcategory", "price",
#     "listprice", "discountprice", "supplier", "product_availability", "eta"
# ]

# # Create DataFrame and export
# df = pd.DataFrame(data, columns=columns)
# df.to_csv("product_table_structured_ids.csv", index=False)
# print("CSV file 'product_table_structured_ids.csv' generated successfully.")


# import pandas as pd
# import numpy as np
# from faker import Faker
# import random

# # Initialize Faker
# fake = Faker()

# # Load your product catalog CSV
# product_data = pd.read_csv("product_catalog.csv")  # Make sure the file path is correct

# # Generate fake order data
# num_orders = 100  # Adjust as needed
# order_data = []

# payment_methods = ['Credit Card', 'Debit Card', 'Paypal']

# for _ in range(num_orders):
#     product = product_data.sample(1).iloc[0]
    
#     # Generate a full address
#     city = fake.city()
#     state = fake.state()
#     country = fake.country()
#     pincode = fake.postcode()
#     full_location = f"{city}, {state}, {country} - {pincode}"
    
#     order = {
#         "order_placement": fake.date_time_between(start_date='-30d', end_date='now'),
#         "customer_name": fake.name(),
#         "time_of_order": fake.time(),
#         "location": full_location,
#         "product_id": product['product_id'],
#         "quantity": random.randint(1, 5),
#         "payment_method": random.choice(payment_methods)
#     }
#     order_data.append(order)

# # Convert to DataFrame
# orders_df = pd.DataFrame(order_data)

# # Save or inspect the result
# orders_df.to_csv("order_data.csv", index=False)
# print(orders_df.head())


import pandas as pd
import numpy as np
from faker import Faker
import random

# Load your data (replace with your actual file names if needed)
orders = pd.read_csv('order_data.csv')
products = pd.read_csv('product_catalog.csv')

fake = Faker()

# Merge orders and products on product_id
shipping = pd.merge(orders, products, on='product_id', how='left')

# Status options
on_time_statuses = ["Order Received", "Processing", "In Transit", "Out for Delivery", "Delivered"]
delayed_statuses = ["Delayed", "Cancelled"]

# Helper functions
def random_status(delayed=False):
    if delayed:
        return random.choice(delayed_statuses)
    else:
        # Most will be delivered or in progress
        return random.choices(
            ["Delivered", "In Transit", "Out for Delivery", "Processing", "Order Received"],
            weights=[50, 20, 10, 10, 10], k=1
        )[0]

def random_carrier():
    return fake.company()

def random_tracking():
    return fake.bothify(text='???-########')

# Generate shipment and delivery dates
shipment_dates = []
estimated_deliveries = []
actual_deliveries = []
statuses = []

for idx, row in shipping.iterrows():
    order_dt = pd.to_datetime(row['order_placement'])
    # 80% on time, 20% delayed
    is_delayed = random.random() < 0.2
    # Shipment happens 0-2 days after order
    ship_delay = random.randint(0, 2)
    shipment_date = order_dt + pd.Timedelta(days=ship_delay)
    # Estimated delivery 2-7 days after shipment
    delivery_delay = random.randint(2, 7)
    estimated_delivery = shipment_date + pd.Timedelta(days=delivery_delay)
    # If delayed, actual delivery is 1-3 days after estimated, else on time
    if is_delayed:
        status = random_status(delayed=True)
        actual_delivery = estimated_delivery + pd.Timedelta(days=random.randint(1, 3)) if status == "Delayed" else np.nan
    else:
        status = random_status(delayed=False)
        actual_delivery = estimated_delivery if status == "Delivered" else np.nan

    shipment_dates.append(shipment_date.strftime('%Y-%m-%d'))
    estimated_deliveries.append(estimated_delivery.strftime('%Y-%m-%d'))
    actual_deliveries.append(actual_delivery.strftime('%Y-%m-%d') if pd.notnull(actual_delivery) else "")
    statuses.append(status)

shipping['carrier'] = [random_carrier() for _ in range(len(shipping))]
shipping['tracking_number'] = [random_tracking() for _ in range(len(shipping))]
shipping['shipment_date'] = shipment_dates
shipping['estimated_delivery'] = estimated_deliveries
shipping['actual_delivery'] = actual_deliveries
shipping['status'] = statuses

# Select and order columns for output
cols = [
    'order_placement', 'customer_name', 'time_of_order', 'location',
    'product_id', 'product_category', 'product_subcategory', 'quantity',
    'payment_method', 'price', 'supplier', 'carrier', 'tracking_number',
    'shipment_date', 'estimated_delivery', 'actual_delivery', 'status'
]
shipping = shipping[cols]

# Save to CSV
shipping.to_csv('shipping_logistics.csv', index=False)
print("shipping_logistics.csv created with all mapped and logistics fields.")

