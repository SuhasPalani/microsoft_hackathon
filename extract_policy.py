from PyPDF2 import PdfReader

# Load the policy PDF
reader = PdfReader("Company_Policy_Logistics.pdf")

# Extract text from all pages
policy_text = "\n".join([page.extract_text() for page in reader.pages])

# Save as plain text for RAG use
with open("policy_clauses.txt", "w") as f:
    f.write(policy_text)

print("✅ Policy text extracted and saved to data/policy_clauses.txt")


