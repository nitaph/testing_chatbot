import streamlit as st
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid

# --- Set up API keys ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Google Sheets setup ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client_gspread = gspread.authorize(creds)
try:
    sheet = client_gspread.open("ChatbotConversations").worksheet("conversations")
except gspread.exceptions.WorksheetNotFound:
    sheet = client_gspread.open("ChatbotConversations").add_worksheet(title="conversations", rows=100, cols=4)

# --- Session management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

st.title("🧠 ‘Imagine a world where humans have just made contact with extraterrestrial beings. The first meeting happens in a small town, and the townspeople are unsure how to react. Describe the emotions, interactions, and events that unfold during this historic encounter.’")

# --- Display previous chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User input ---
user_input = st.chat_input("Ask something...")
if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Create conversation history
    conversation_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    # Get assistant response using OpenAI API
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150
        )
        reply = response.choices[0].message.content.strip()
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
    except Exception as e:
        st.error(f"⚠️ Error with OpenAI API: {e}")
        reply = None

    # --- Save conversation to Google Sheets ---
    if reply:
        try:
            sheet.append_row([
                datetime.utcnow().isoformat(),
                st.session_state.session_id,
                "user",
                user_input
            ])
            sheet.append_row([
                datetime.utcnow().isoformat(),
                st.session_state.session_id,
                "assistant",
                reply
            ])
            st.success("✅ Conversation saved to Google Sheets!")
        except Exception as e:
            st.error(f"⚠️ Error saving to Google Sheets: {e}")
