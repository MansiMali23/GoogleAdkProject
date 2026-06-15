"""
kb.py — Tiny ChromaDB-backed knowledge base for semantic search & RAG
------------------------------------------------------------------------
Concept: Module 5 — Semantic Search and Retrieval-Augmented Generation

The pipeline, end to end, in one short file:

    1. Embed every document once (OpenRouter's OpenAI embedding endpoint
       via LiteLlm — the same provider as the chat model, see agent.py)
       and upsert them into an in-memory ChromaDB collection.
    2. Embed the incoming query the same way.
    3. Ask ChromaDB for the top_k nearest documents by vector distance.

ChromaDB runs here as an *ephemeral*, in-process client — no server, no
files left on disk — which keeps the demo a one-command `python demo.py`
while still showing the real article: a vector database doing the
similarity search, not a hand-rolled loop.

For a persistent, production-shaped version of this same idea — a larger
catalog, on-disk storage, metadata filtering — see the RAG layer in
lab/ecombot/rag/ (embed_catalog.py + retriever.py).
"""

import os

import chromadb
import litellm
from dotenv import load_dotenv

load_dotenv()
litellm.suppress_debug_info = True

EMBEDDING_MODEL = "openrouter/openai/text-embedding-3-small"
COLLECTION_NAME = "day05_e-commerce_kb"

# ── Knowledge base ──────────────────────────────────────────────────────────
# A handful of short e-commerce-tip documents. The last two are eComBot-specific
# "policies" that no general-purpose model could already know — they're what
# make Scenario 2 in demo.py convincing: when the agent gets these right, it's
# clearly because it retrieved them, not because it was trained on them.
DOCUMENTS: list[dict[str, str]] = [
    {
        "id": "product-warranty-guide",
        "text": (
            "All electronics purchased through eComBot come with a standard one-year "
            "manufacturer's warranty covering defects in materials and workmanship. "
            "Extended warranty options are available at checkout. Warranty does not "
            "cover accidental damage, misuse, or normal wear and tear."
        ),
    },
    {
        "id": "shipping-options-explained",
        "text": (
            "Standard shipping (5-7 business days) is free on orders over $50. Express "
            "shipping (2-3 business days) costs $9.99. Next-day shipping is available "
            "for $24.99 in most areas. All shipments are tracked and insured. Orders "
            "typically ship within 24 hours of purchase."
        ),
    },
    {
        "id": "returns-and-refunds-policy",
        "text": (
            "eComBot offers a 30-day money-back guarantee on most items. To initiate a "
            "return, log into your account, select the order, and request a return label. "
            "Once the item arrives at our warehouse in resalable condition, your refund is "
            "processed within 5-7 business days. Return shipping is free on refunds due to "
            "defects; otherwise, return shipping is the customer's responsibility."
        ),
    },
    {
        "id": "payment-methods-security",
        "text": (
            "We accept all major credit and debit cards, PayPal, Apple Pay, and Google Pay. "
            "All transactions are encrypted using industry-standard SSL technology. Your "
            "payment information is never stored on our servers — it is processed securely "
            "through PCI-DSS compliant gateways. We also offer a 0% APR payment plan through "
            "Affirm for purchases over $50."
        ),
    },
    {
        "id": "product-categories-guide",
        "text": (
            "Our catalog spans electronics (laptops, phones, tablets), home and garden, "
            "sports and outdoors, fashion, and books. Within each category, products are "
            "sorted by customer ratings, price, and newest releases. Use our advanced "
            "filters to narrow by brand, features, price range, and availability. Many "
            "categories offer exclusive deals on select items."
        ),
    },
    {
        "id": "bulk-order-discounts",
        "text": (
            "Orders of 10+ units qualify for bulk discounts. The discount tier increases "
            "with order size: 10-24 units get 10% off, 25-49 units get 15% off, and 50+ "
            "units get 20% off. Bulk orders ship to a single address and cannot be split. "
            "Contact our B2B team for custom quotes on very large orders."
        ),
    },
    {
        "id": "ecombot-loyalty-program",
        "text": (
            "eComBot Rewards members earn 1 point per dollar spent on all purchases. "
            "Points can be redeemed for discounts or free items. VIP members (those who "
            "spend over $500 annually) earn double points and get early access to sales. "
            "VIP status is reviewed annually based on total spending in the prior 12 months."
        ),
    },
    {
        "id": "ecombot-free-shipping-policy",
        "text": (
            "Free standard shipping (5-7 business days) applies to all orders over $50 "
            "within the continental US. eComBot Pro members get free expedited shipping "
            "on all orders. Orders placed before 2 PM ET typically ship the same business "
            "day; otherwise, they ship within 24 hours. Free returns are available for "
            "defective items."
        ),
    },
]


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via OpenRouter's OpenAI-compatible /embeddings endpoint."""
    response = litellm.embedding(
        model=EMBEDDING_MODEL,
        input=texts,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    return [item["embedding"] for item in response.data]


# Opened once per process — building the collection means embedding every
# document, so it's worth caching the client/collection as a singleton.
_collection = None


def _get_collection():
    """Return the (lazily indexed) in-memory ChromaDB collection of DOCUMENTS."""
    global _collection
    if _collection is None:
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        collection.upsert(
            ids=[doc["id"] for doc in DOCUMENTS],
            documents=[doc["text"] for doc in DOCUMENTS],
            embeddings=embed([doc["text"] for doc in DOCUMENTS]),
        )
        _collection = collection
    return _collection


def semantic_search(query: str, top_k: int = 3) -> list[dict]:
    """
    Return the top_k documents whose embeddings are closest — by vector
    distance, as judged by ChromaDB — to the query's embedding.

    Each result is a dict: {"id", "text", "score"} where score is a
    similarity in [0, 1] derived from ChromaDB's distance (higher = closer
    match), so callers don't need to know which distance metric is in use.
    Returns an empty list for an empty query.
    """
    if not query or not query.strip():
        return []

    collection = _get_collection()
    result = collection.query(
        query_embeddings=embed([query.strip()]),
        n_results=min(top_k, collection.count()),
    )

    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    return [
        {"id": doc_id, "text": text, "score": 1.0 / (1.0 + distance)}
        for doc_id, text, distance in zip(ids, documents, distances)
    ]
