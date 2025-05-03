import os
import pathway as pw

# Define schemas

class ProductSchema(pw.Schema):
    product_id: str
    name: str
    category: str
    price: float

class OrderSchema(pw.Schema):
    order_id: str
    product_id: str
    customer: str
    quantity: int

class ShippingSchema(pw.Schema):
    shipment_id: str
    order_id: str
    carrier: str
    origin: str
    destination: str
    status: str
    last_update: str

# Read all CSVs (streaming mode, batching every 5 seconds)
products = pw.io.csv.read(
    "live_product_catalog.csv",
    schema=ProductSchema,
    mode="streaming",
    autocommit_duration_ms=5000
)
orders = pw.io.csv.read(
    "live_order_data.csv",
    schema=OrderSchema,
    mode="streaming", 
    autocommit_duration_ms=5000
)
shipping = pw.io.csv.read(
    "live_shipping_logistics.csv",
    schema=ShippingSchema,
    mode="streaming",
    autocommit_duration_ms=5000
)

# Join: orders + products
order_product = orders.join(
    products,
    orders.product_id == products.product_id
).select(
    order_id=pw.left.order_id,
    product_id=pw.left.product_id,
    customer=pw.left.customer,
    quantity=pw.left.quantity,
    product_name=pw.right.name,
    category=pw.right.category,
    price=pw.right.price
)

# Join: (orders+products) + shipping
full_data = order_product.join(
    shipping,
    order_product.order_id == shipping.order_id
).select(
    shipment_id=pw.right.shipment_id,
    order_id=pw.left.order_id,
    product_name=pw.left.product_name,
    quantity=pw.left.quantity,
    customer=pw.left.customer,
    destination=pw.right.destination,
    status=pw.right.status,
    carrier=pw.right.carrier,
    origin=pw.right.origin,
    last_update=pw.right.last_update
)

# Generate RAG documents
rag_docs = full_data.select(
    shipment_id=pw.this.shipment_id,
    text=(
        "Status: " + pw.this.status +
        " | Destination: " + pw.this.destination +
        " | Product: " + pw.this.product_name +
        " | Customer: " + pw.this.customer +
        " | Carrier: " + pw.this.carrier
    )
)

# Ensure output directory exists
os.makedirs("output", exist_ok=True)

# Write JSONL output
pw.io.jsonlines.write(rag_docs, "output/shipping_docs.jsonl")

# Run the pipeline
pw.run()
