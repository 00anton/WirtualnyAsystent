import os
import shutil
from fastapi import FastAPI
from pydantic import BaseModel
from rag import get_chat_engine, build_index

app = FastAPI()

try:
    if os.path.exists("storage"):
        chat_engine = get_chat_engine()
    else:
        chat_engine = None
except Exception:
    chat_engine = None


class Question(BaseModel):
    question: str


@app.post("/chat")
def chat(question: Question):
    global chat_engine
    if chat_engine is None:
        return {"response": "Brak dokumentów. Wgraj najpierw pliki PDF."}
    response = chat_engine.chat(question.question)
    return {"response": str(response)}


@app.post("/rebuild")
async def rebuild():
    global chat_engine
    from fastapi.concurrency import run_in_threadpool
    if os.path.exists("storage"):
        shutil.rmtree("storage")
    await run_in_threadpool(build_index)
    chat_engine = await run_in_threadpool(get_chat_engine)
    return {"status": "ok"}

class Filename(BaseModel):
    filename: str


@app.post("/delete")
async def delete_file(file: Filename):
    global chat_engine
    from fastapi.concurrency import run_in_threadpool
    file_path = os.path.join("data", file.filename)
    if not os.path.exists(file_path):
        return {"status": "error", "message": "Plik nie istnieje"}
    os.remove(file_path)
    if os.path.exists("storage"):
        shutil.rmtree("storage")
    remaining = os.listdir("data")
    if remaining:
        await run_in_threadpool(build_index)
        chat_engine = await run_in_threadpool(get_chat_engine)
    else:
        chat_engine = None
    return {"status": "ok"}