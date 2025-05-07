import streamlit as st
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid

# --- Set up API keys ---
openai.api_key = st.secrets["OPENAI_API_KEY"]  # Use secret for OpenAI API key

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client_gspread = gspread.authorize(creds)
sheet = client_gspread.open("ChatbotConversations").worksheet("conversations")  # Sheet must exist!

# --- Session management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

st.title("🧠 Imagine a world where humans have just made contact with extraterrestrial beings. The first meeting happens in a small town, and the townspeople are unsure how to react. Describe the emotions, interactions, and events that unfold during this historic encounter.")

# --- Display previous chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User input ---
prompt = st.chat_input("Ask something...")
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Create conversation history
    conversation_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    # Get assistant response using OpenAI API (corrected API call)
    response = openai.Completion.create(
        model="gpt-3.5-turbo",  # or "gpt-4" if you have access
        prompt=conversation_history,  # Use the conversation history for the chat
        max_tokens=150  # Adjust this based on your needs
    )

    # Get the assistant's reply
    reply = response['choices'][0]['text'].strip()
    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)

    # --- Save conversation to Google Sheets automatically after every message ---
    try:
        for msg in st.session_state.messages:
            sheet.append_row([
                datetime.utcnow().isoformat(),
                st.session_state.session_id,
                msg["role"],
                msg["content"]
            ])
        st.success("✅ Conversation saved to Google Sheets!")
    except Exception as e:
        st.error(f"⚠️ Error saving to Google Sheets: {e}")
