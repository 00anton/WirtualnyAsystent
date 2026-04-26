import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings

load_dotenv()

DATA_DIR = 'data'
STORAGE_DIR = "storage"

Settings.llm = OpenAI(model="gpt-4.1-mini")

def build_index():
    """Tworzy indeks z dokumentów PDF i zapisuje go na dysku."""
    files = os.listdir(DATA_DIR)
    if not files:
        raise ValueError("Folder 'data/' jest pusty. Dodaj dokumenty PDF przed uruchomieniem.")
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    index = VectorStoreIndex.from_documents(
        documents,
        chunk_size=1024,
        chunk_overlap=200
    )
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    return index

def load_index():

    storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
    index = load_index_from_storage(storage_context)
    return index

def get_index():

    if os.path.exists(STORAGE_DIR):
        return load_index()
    else:
        return build_index()

def get_chat_engine():
    """Zwraca gotowy silnik czatu."""
    index = get_index()
    return index.as_chat_engine(
        chat_mode="condense_plus_context",
        system_prompt=(
            "Jesteś asystentem odpowiadającym wyłącznie na podstawie dostarczonych dokumentów. "
            "Jeśli odpowiedź na pytanie nie znajduje się w dokumentach, powiedz że nie posiadasz "
            "takiej informacji w dostępnych dokumentach i nie próbuj odpowiadać na podstawie "
            "własnej wiedzy. Nie odpowiadaj na pytania niezwiązane z dokumentami."
        )
    )
