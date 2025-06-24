import json
import chromadb
import lmstudio as lms
from pathlib import Path
from chromadb.config import Settings

'''
chroma_client = chromadb.PersistentClient(path="../database.chroma")
collection1 = chroma_client.get_or_create_collection(name="my_collection")
'''
import sqlite3
DB_FILE = Path(__file__).resolve().parent.parent / "database.chroma" / "chroma.sqlite3"
conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()
print(cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())

CHROMA_DIR = Path(__file__).resolve().parent.parent / "database.chroma"

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),          # MUST be a directory, not the *.sqlite3 file
    settings=Settings(anonymized_telemetry=False)  # optional
)
collection = client.get_collection("my_collection")

documents = []
ids = []
metadatas = []


model = lms.llm("ibm/granite-3.1-8b")

'''
# Open the JSONL-style file (one JSON object per line)
with open("../../sample_data/api_descriptions_deepseek_coder_6pt7b.json", "r") as f:
    for i, line in enumerate(f):
        api = json.loads(line.strip())  # Parse each line as a JSON object

        file = api["file"]
        endpoints = api.get("endpoints", "Empty")
        summary = endpoints.get("api_summary", "Empty")
        methods = str(endpoints.get("methods", "Empty"))
        paths = str(endpoints.get("paths", "Empty"))



        documents.append(summary)
        print()
        ids.append(f"id_{i}")
        metadatas.append({
            "file": file,
            "methods": methods,
            "paths": paths
        })
        print(i)


print("Document Length:", len(documents))
# Upsert into the Chroma collection


#Uncomment when we want to update database
collection1.upsert(
    documents=documents,
    ids=ids,
    metadatas=metadatas
)
'''
print("Database Created")


def find_similar_apis(text_input, top_k):

    print("finding similar apis")
    results = collection.query(
    query_texts=[text_input],
    n_results=top_k
    )
    print("Found similar apis")
    return results

def parse_rag_response(rag_response):
    """
    Parses a RAG response and returns a list of tuples with (file, document) in order.
    """
    print("parsing rag")
    documents = rag_response['documents'][0]
    metadatas = rag_response['metadatas'][0]

    if len(documents) != len(metadatas):
        raise ValueError("Mismatch between number of documents and metadata entries.")

    result = []
    for doc, meta in zip(documents, metadatas):
        file = meta.get('file', 'UNKNOWN FILE')
        result.append((file, doc))

    return result

api_descriptions = [
    'User Registration: Allows a client to create a new user account by providing basic profile details (name, email, password) and returns the newly created user’s ID and creation timestamp.',
    'User Authentication: Validates a user’s credentials and issues a short-lived access token plus a refresh token for subsequent calls.',
    'Token Refresh: Exchanges a valid refresh token for a new access token, extending the user’s session without re-authentication.',
    'Fetch User Profile: Retrieves all stored profile information (name, email, preferences, roles) for a given user ID.',
    'Update User Preferences: Lets users modify their notification settings, language, or other personalization options and returns the updated preferences.',
    'Place Order: Accepts a list of product identifiers and quantities for a user, creates a new order, reserves inventory, and returns the order confirmation with status “pending.”',
    'Get Order Status: Provides the current status, timestamps, and line-item details for an existing order by its ID.',
    'List User Orders: Returns a chronological list of all orders placed by a particular user, including brief summaries of each (status, total amount).',
    'Cancel Order: Requests cancellation of an order that hasn’t shipped yet and updates its status accordingly.',
    'Add Item to Shopping Cart: Adds a specified product and quantity to a user’s active shopping cart, creating the cart if it doesn’t already exist.',
    'View Shopping Cart: Retrieves the entire contents of a user’s shopping cart, including item details, quantities, and subtotal.',
    'Remove Item from Cart: Deletes a specific item from the user’s shopping cart and returns the updated cart contents.',
    'Checkout Cart: Converts all items in the user’s cart into a formal order, triggers payment processing, and returns the new order’s ID.',
    'Search Products: Allows free-text search over product catalog data and returns matching products with key attributes like price and stock level.',
    'Get Product Details: Fetches complete details (description, images, specifications) for a specific product by its identifier.',
    'Adjust Inventory Levels: Increases or decreases stock counts for a product after shipments arrive or returns are processed.',
    'Reserve Inventory for Order: Temporarily locks stock for a pending order to prevent overselling, with an automatic expiry if not confirmed.',
    'Process Payment: Charges a specified payment method (e.g., credit card) for an order amount and returns a payment transaction record.',
    'Issue Refund: Initiates a refund for a previously completed payment, returning a refund transaction ID and updated status.',
    'Create Shipment: Schedules a shipment for a confirmed order, assigns a courier service, and returns tracking information.',
    'Track Shipment: Retrieves the real-time delivery status and estimated arrival for a given shipment identifier.',
    'Send Notification: Dispatches an email or SMS notification to a user based on events (order confirmation, shipping update), and returns a notification log entry.',
    'Subscribe to Webhook Events: Registers an external endpoint to receive real-time callbacks when specified domain events occur (e.g., order updates).',
    'Publish Domain Event: Emits an internal event (e.g., "order.completed") to notify other microservices of changes in state.',
    'Fetch Service Metrics: Provides key performance indicators—such as request count, error rate, and latency percentiles—for a specific microservice.',
    'Health Check: Returns a simple "OK" status and uptime information for orchestration systems to verify the service is alive and ready.',
    'Schedule Report Generation: Initiates an asynchronous job to compile business reports (sales, inventory) over a given date range and returns a job ID.',
    'Check Report Status: Queries the current progress of a report-generation job and, when complete, provides a download link.',
    'Validate Discount Code: Confirms whether a promotional code is valid for an order and calculates the discounted total.',
    'Log Audit Entry: Records critical user or system actions (e.g., "user.updated.profile") into an append-only audit log for compliance.'
]



prompt = """
You are a senior software engineer assistant. A developer has provided an API feature request (INPUT API), and your job is to review both internal APIs (RECOMMENDED INTERNAL APIs) and relevant open-source examples (OPTIONAL EXTERNAL APIs) to offer specific, implementation-level guidance.

For each recommended API (internal or external), respond using this format:

---
**Source:** <file path or GitHub URL>
**Summary:** <1–2 sentence summary of what the code does, based on filename and contents.>
**Implementation Guidance:**
- Explain how this code is related to the INPUT API functionality.
- Reference specific function names, classes, or logic.
- Avoid generic phrases — clearly map features from this code to possible components in the INPUT API.
- If external, suggest how this repo might be used as a reference only (not directly imported).
---

**Rules:**
- Be concise but technically detailed.
- For INTERNAL APIs: treat them as available for direct use.
- For EXTERNAL APIs: treat them as optional *inspiration only* — do not assume they are installed or imported.
- Avoid generalities like “create a task queue” unless directly supported by the source code.
- Do not mention proprietary APIs (e.g., Stripe, Twitter).
- Use only the provided materials.

### INPUT API
{input_api}

### RECOMMENDED INTERNAL APIs (with code excerpts)
{recommended_apis}


**Final Instructions:**
- Include **all internal APIs** in your response unless clearly irrelevant.
- Do **not** restate features (e.g., “this has user registration”); explain how they are implemented.
"""

with open("Vanilla_Retreival.txt", "w") as output_file:
    for i, api in enumerate(api_descriptions):

        recommended = find_similar_apis(api,1)
        print("Rag Response:", recommended)
        input_text = prompt.format(
        input_api = api,
        recommended_apis = recommended,
        )
        response = model.respond(input_text)
        print(response)
        output_file.write(f'input api description #{i}: \n \n" {api} \n "recommended APIs:" {str(response)} \n')
