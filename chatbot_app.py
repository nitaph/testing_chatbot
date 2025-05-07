import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

# 1. Load API keys and credentials from Streamlit secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]            # OpenAI API key
service_account_info = st.secrets["gcp_service_account"] # Google service account JSON
sheet_url = st.secrets["private_gsheets_url"]            # URL of the target Google Sheet

# 2. Initialize OpenAI API client (using new OpenAI SDK v1.77+ syntax)
client = OpenAI(api_key=openai_api_key)  # Set API key (could also rely on OPENAI_API_KEY env var):contentReference[oaicite:5]{index=5}

# 3. Initialize Google Sheets client via gspread
# Define scope for Google Sheets and authorize credentials
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)  # use service account info:contentReference[oaicite:6]{index=6}
gs_client = gspread.authorize(credentials)  # authenticate with gspread using the credentials:contentReference[oaicite:7]{index=7}

# Open the Google Sheet (by URL)
try:
    sh = gs_client.open_by_url(sheet_url)
    worksheet = sh.sheet1  # use the first sheet; or use sh.worksheet("SheetName") if needed
except Exception as e:
    st.error(f"Error opening Google Sheet: {e}")
    st.stop()

# 4. Initialize chat history in session state (with optional system prompt for context)
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Optionally add a system role message to set the assistant's behavior:
    st.session_state.messages.append({"role": "system", "content": "You are a helpful assistant."})

# 5. Display existing conversation messages (if any) using Streamlit's chat message containers
for msg in st.session_state.messages:
    # Skip displaying the system message to the UI (it's for the model only)
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 6. Chat input widget for the user to type a new message
user_input = st.chat_input("Type your message here...")
if user_input:
    # Add the new user message to the chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Display the user message immediately in the app
    with st.chat_message("user"):
        st.write(user_input)
    # Call the OpenAI chat completion API with the full message history:contentReference[oaicite:8]{index=8}
    with st.spinner("Assistant is typing..."):  # show a spinner while waiting for response
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",                 # or "gpt-4" if available
                messages=st.session_state.messages    # send the entire conversation history
            )
        except Exception as api_error:
            st.error(f"OpenAI API error: {api_error}")
            st.stop()
    # Extract the assistant's reply from the response
    assistant_reply = response.choices[0].message.content
    # Add the assistant response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    # Display the assistant response in the app
    with st.chat_message("assistant"):
        st.write(assistant_reply)
    # 7. Log the user query and assistant response to the Google Sheet
    try:
        worksheet.append_row([user_input, assistant_reply], value_input_option="RAW")
    except Exception as sheet_error:
        st.warning(f"Could not log to Google Sheet: {sheet_error}")
