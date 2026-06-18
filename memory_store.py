import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    MemoryStoreDefaultDefinition,
    MemoryStoreDefaultOptions,
)

memory_store_name = "memory_store-agent-cuhk"

# Specify memory store options
options = MemoryStoreDefaultOptions(
    chat_summary_enabled=True,
    user_profile_enabled=True,
    procedural_memory_enabled=True,
    default_ttl_seconds=30 * 24 * 60 * 60,
    user_profile_details="Avoid irrelevant or sensitive data, such as age, financials, precise location, and credentials",
)

# Create memory store
chat_model = os.environ["MEMORY_STORE_CHAT_MODEL_DEPLOYMENT_NAME"]
embedding_model = os.environ["MEMORY_STORE_EMBEDDING_MODEL_DEPLOYMENT_NAME"]

definition = MemoryStoreDefaultDefinition(
    chat_model=chat_model, embedding_model=embedding_model, options=options
)

memory_store = project_client.beta.memory_stores.create(
    name=memory_store_name,
    definition=definition,
    description="Memory store with procedural memory and 30-day default TTL",
)

print(f"Created memory store: {memory_store.name}")
