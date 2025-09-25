import getpass
import os
from dotenv import load_dotenv
load_dotenv()

if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google: ")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
print(f"Connecting to Redis at: {REDIS_URL}")

import redis

redis_client = redis.from_url(REDIS_URL)
print("Connected to Redis: ", redis_client.ping())

from datetime import datetime
import uuid

# Sample memory data for different users
memory_texts = [
    "Alice loves spending weekends hiking in the mountains",
    "Bob remembers his first concert was a rock band in 2019",
    "Alice had a great dinner at the Italian restaurant downtown",
    "Charlie learned Python programming during the pandemic",
    "Bob enjoys reading science fiction novels before bed",
    "Alice's favorite coffee shop is on Main Street",
    "Charlie completed a marathon last year in 3 hours",
    "Bob's childhood pet was a golden retriever named Max",
    "Alice prefers working from home on Mondays",
    "Charlie visited Japan and loved the cherry blossoms"
]

# Generate metadata for each memory
users = ["alice", "bob", "charlie"]
memory_types = ["personal", "hobby", "work", "travel", "food"]
timestamps = [
    "2024-01-15", "2024-02-10", "2024-03-05", "2024-04-20", "2024-05-12",
    "2024-06-18", "2024-07-25", "2024-08-30", "2024-09-14", "2024-10-22"
]

metadata = []
for i, text in enumerate(memory_texts):
    user = "alice" if "Alice" in text else "bob" if "Bob" in text else "charlie"
    mem_type = "personal" if i % 3 == 0 else "hobby" if i % 3 == 1 else "travel"
    metadata.append({
        "id": str(uuid.uuid4())[:8],
        "userId": user,
        "type": mem_type,
        "created_at": timestamps[i]
    })

texts = memory_texts
print(f"Created {len(texts)} memory entries")


from langchain_redis import RedisConfig, RedisVectorStore

config = RedisConfig(
    index_name="memories",
    redis_url=REDIS_URL,
    metadata_schema=[
        {"name": "id", "type": "tag"},
        {"name": "userId", "type": "tag"},
        {"name": "type", "type": "tag"},
        {"name": "created_at", "type": "text"},
    ],
)


from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = RedisVectorStore(embeddings, config=config)

ids = vector_store.add_texts(texts, metadata)

print(ids[0:10])

print(f"Sample memory: {texts[0]}")
print(f"Sample metadata: {metadata[0]}")

# Test memory retrieval with different queries
queries = [
    "What does Alice like to do on weekends?",
    "Tell me about Bob's hobbies",
    "What travel experiences are remembered?"
]

for query in queries:
    print(f"\n--- Query: {query} ---")
    results = vector_store.similarity_search_with_score(query, k=2)

    for i, (doc, score) in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Memory: {doc.page_content}")
        print(f"  User: {doc.metadata.get('userId', 'unknown')}")
        print(f"  Type: {doc.metadata.get('type', 'unknown')}")
        print(f"  Date: {doc.metadata.get('created_at', 'unknown')}")
        print(f"  Score: {score:.4f}")
        print()

# Test user-specific memory retrieval
print("\n--- User-specific search for Alice ---")
user_results = vector_store.similarity_search("weekends hobbies preferences", k=5)
for doc in user_results:
    if doc.metadata.get('userId') == 'alice':
        print(f"Alice's memory: {doc.page_content}")
        print(f"  Type: {doc.metadata.get('type')}")
        print(f"  Date: {doc.metadata.get('created_at')}")
        print()

# Test retriever functionality for memory queries
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
print("\n--- Retriever Results ---")
retriever_results = retriever.invoke("what does alice remember?")
for doc in retriever_results:
    print(f"Memory: {doc.page_content}")
    print(f"User: {doc.metadata.get('userId')}")
    print()

