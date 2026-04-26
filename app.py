import streamlit as st
import requests
import os
from rag import get_chat_engine

try:
    chat_engine = get_chat_engine()
    engine_ready = True
except ValueError as e:
    engine_ready = False
    engine_error = str(e)

API_URL = "http://localhost:8000/chat"

st.title("Wirtualny Asystent")
st.write("Zadaj pytanie do bazy dokumentów.")

st.subheader("Wgraj dokumenty PDF")
uploaded_files = st.file_uploader(
    "Wybierz pliki PDF",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    new_files = False
    for uploaded_file in uploaded_files:
        file_path = os.path.join("data", uploaded_file.name)
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            new_files = True
    if new_files:
        st.success(f"Wgrano nowe pliki. Przebudowuję indeks...")
        requests.post("http://localhost:8000/rebuild")
        st.rerun()
    else:
        st.info("Te pliki są już wgrane.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not engine_ready:
    st.error(engine_error)
    st.stop()

if prompt := st.chat_input("Wpisz pytanie..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Szukam odpowiedzi..."):
            try:
                response = requests.post(API_URL, json={"question": prompt})
                answer = response.json()["response"]
            except Exception:
                answer = "Błąd połączenia z serwerem. Sprawdź czy backend działa."
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})