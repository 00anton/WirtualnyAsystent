import streamlit as st
import requests
import os
import json

st.markdown("""
    <style>
    section[data-testid="stSidebar"] div.stButton > button {
        padding: 0px 4px;
        font-size: 10px;
        height: 1.5rem;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000/chat"
HISTORY_FILE = "chat_history.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


st.title("Wirtualny Asystent")
st.write("Zadaj pytanie do bazy dokumentów.")

# Wgrywanie plików
with st.sidebar:
    st.subheader("Wgraj dokumenty PDF")

    # Komunikat po usunięciu
    if "delete_message" in st.session_state:
        msg = st.session_state.delete_message
        if msg == "rebuilt":
            st.success("Indeks został przebudowany.")
        elif msg == "cleared":
            st.warning("Usunięto ostatni dokument. Indeks został wyczyszczony.")
        del st.session_state.delete_message

    # Lista wgranych plików
    files_in_data = os.listdir("data")
    if files_in_data:
        st.write("**Wgrane pliki:**")
        for file in files_in_data:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                    <p style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin: 6px 0;">
                    📄 {file}
                    </p>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("❌", key=file, help=f"Usuń {file}", type="tertiary", width="content"):
                    requests.post("http://localhost:8000/delete",
                                  json={"filename": file})
                    remaining = os.listdir("data")
                    if remaining:
                        st.session_state.delete_message = "rebuilt"
                    else:
                        st.session_state.delete_message = "cleared"
                    st.rerun()
    else:
        st.info("Brak wgranych plików.")

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    uploaded_files = st.file_uploader(
        "Wybierz pliki PDF",
        type="pdf",
        accept_multiple_files=True,
        key=st.session_state.uploader_key
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
            st.session_state.uploader_key += 1
            st.success("Wgrano nowe pliki. Przebudowuję indeks...")
            requests.post("http://localhost:8000/rebuild")
            st.rerun()
        else:
            st.info("Te pliki są już wgrane.")

    st.divider()

    if st.button("Wyczyść historię czatu"):
        st.session_state.messages = []
        save_history([])
        st.rerun()


# Ładowanie historii przy starcie
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# Wyświetlanie historii
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Czat
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
    save_history(st.session_state.messages)