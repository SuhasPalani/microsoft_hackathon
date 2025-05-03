import pathway as pw

class ShippingSchema(pw.Schema):
    shipment_id: str
    product_id: str
    carrier: str
    origin: str
    destination: str
    status: str
    last_update: str

# Use schema only — no 'columns' or 'has_header'
shipping = pw.io.csv.read(
    "live_shipping.csv",
    schema=ShippingSchema,
    mode="streaming"
)

rag_docs = shipping.select(
    text=pw.this.status + " | " + pw.this.destination,
    shipment_id=pw.this.shipment_id
)

pw.io.jsonlines.write(rag_docs, "output/shipping_docs.jsonl")
pw.run()
