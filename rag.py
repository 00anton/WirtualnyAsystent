import os
from pathlib import Path
from dotenv import load_dotenv
import docx2txt
from odf import teletype
from odf.opendocument import load as load_odt
from odf.text import P, H
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings, Document

load_dotenv()

DATA_DIR = 'data'
STORAGE_DIR = "storage"

Settings.llm = OpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))


def read_odt(file_path: str) -> str:
    """Odczytuje tekst z pliku ODT."""
    odt_doc = load_odt(file_path)
    text_parts = []
    for element in odt_doc.getElementsByType(H):
        text_parts.append(teletype.extractText(element))
    for element in odt_doc.getElementsByType(P):
        text_parts.append(teletype.extractText(element))
    return "\n".join(text_parts)


def load_documents_from_data_dir():
    """Wczytuje dokumenty PDF, DOCX i ODT z katalogu data."""
    documents = []
    for file_path in Path(DATA_DIR).iterdir():
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            pdf_docs = SimpleDirectoryReader(
                input_files=[str(file_path)]
            ).load_data()
            documents.extend(pdf_docs)
        elif suffix == ".docx":
            text = docx2txt.process(str(file_path))
            if text.strip():
                documents.append(
                    Document(
                        text=text,
                        metadata={"file_name": file_path.name}
                    )
                )
        elif suffix == ".odt":
            text = read_odt(str(file_path))
            if text.strip():
                documents.append(
                    Document(
                        text=text,
                        metadata={"file_name": file_path.name}
                    )
                )
    return documents


def build_index():
    """Tworzy indeks z dokumentów i zapisuje go na dysku."""
    files = os.listdir(DATA_DIR)
    if not files:
        raise ValueError("Folder 'data/' jest pusty. Dodaj dokumenty przed uruchomieniem.")
    documents = load_documents_from_data_dir()
    if not documents:
        raise ValueError("Nie udało się wczytać żadnych dokumentów.")
    index = VectorStoreIndex.from_documents(
        documents,
        chunk_size=1024,
        chunk_overlap=200
    )
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    return index


def load_index():
    """Ładuje istniejący indeks z dysku."""
    storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
    index = load_index_from_storage(storage_context)
    return index


def get_index():
    """Zwraca indeks - ładuje z dysku jeśli istnieje, tworzy jeśli nie."""
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


def get_query_engine():
    """Zwraca silnik zapytań ze źródłami."""
    index = get_index()
    return index.as_query_engine(
        similarity_top_k=3,
    )