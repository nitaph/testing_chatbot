import streamlit as st
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid

# --- Set up OpenAI client (v1+ SDK) ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Google Sheets setup ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client_gspread = gspread.authorize(creds)
sheet = client_gspread.open("ChatbotConversations").worksheet("conversations")

# --- Session management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    # Store your prompt/context as a system message
    st.session_state.system_prompt = (
        "Imagine a world where humans have just made contact with extraterrestrial beings. "
        "The first meeting happens in a small town, and the townspeople are unsure how to react. "
        "Describe the emotions, interactions, and events that unfold during this historic encounter."
    )

# Display as the page title
st.title(f"🧠 {st.session_state.system_prompt}")

# --- Display previous chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User input ---
prompt = st.chat_input("Ask something…")
if prompt:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build messages list, inserting the system prompt first
    api_messages = [
        {"role": "system", "content": st.session_state.system_prompt},
        *st.session_state.messages
    ]

    # Call the new chat completions endpoint
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",    # or "gpt-4"
        messages=api_messages,
        max_tokens=150
    )

    # Extract and display the assistant’s reply
    reply = response.choices[0].message.content.strip()
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

    # --- Persist each turn to Google Sheets ---
    try:
        for m in st.session_state.messages:
            sheet.append_row([
                datetime.utcnow().isoformat(),
                st.session_state.session_id,
                m["role"],
                m["content"],
            ])
        st.success("✅ Conversation saved to Google Sheets!")
    except Exception as e:
        st.error(f"⚠️ Error saving to Google Sheets: {e}")
