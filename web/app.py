import streamlit as st
import requests
from supabase import create_client, Client
import time

# --- CONFIGURATION ---
# REPLACE WITH YOUR ACTUAL KEYS OR USE st.secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"] if "SUPABASE_URL" in st.secrets else "https://zbgdzdytjutujkpdrkzu.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"] if "SUPABASE_KEY" in st.secrets else "sb_publishable_aeOh1O1s1R9ErVtbxY4uKQ_t4RGCRPF"

# REPLACE WITH YOUR RENDER BACKEND URL (No trailing slash)
API_URL = "https://studentai-yl16.onrender.com"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Page Config
st.set_page_config(page_title="Student AI", page_icon="🎓", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_session" not in st.session_state:
    st.session_state.user_session = None
if "profile" not in st.session_state:
    st.session_state.profile = None

# --- SIDEBAR: AUTHENTICATION ---
with st.sidebar:
    st.title("🎓 Student AI")
    
    if st.session_state.user_session is None:
        st.subheader("Login / Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        
        if col1.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user_session = res.session
                st.success("Logged in!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        if col2.button("Register"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("Check your email to confirm!")
            except Exception as e:
                st.error(f"Error: {e}")
                
        if st.button("Continue as Guest"):
             st.session_state.user_session = "GUEST"
             st.rerun()
             
    else:
        # LOGGED IN VIEW
        if st.session_state.user_session != "GUEST":
            user_id = st.session_state.user_session.user.id
            
            # Fetch Profile if not exists
            if not st.session_state.profile:
                try:
                    data = supabase.table("profiles").select("*").eq("id", user_id).execute()
                    if data.data:
                        st.session_state.profile = data.data[0]
                except:
                    pass
            
            st.write(f"**Hello, {st.session_state.profile['full_name'] if st.session_state.profile else 'Student'}!**")
            
            # FILE UPLOADER
            st.subheader("📁 Upload Knowledge")
            uploaded_file = st.file_uploader("Upload PDF/Text notes", type=['txt', 'pdf'])
            
            if uploaded_file and st.button("Process File"):
                with st.spinner("Reading and embedding..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                    data = {"user_id": user_id}
                    try:
                        res = requests.post(f"{API_URL}/upload", files=files, data=data)
                        if res.status_code == 200:
                            st.success("File added to AI Brain!")
                        else:
                            st.error("Upload failed.")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

            if st.button("Logout"):
                supabase.auth.sign_out()
                st.session_state.user_session = None
                st.session_state.profile = None
                st.rerun()
        else:
            st.warning("Guest Mode: Uploads disabled.")
            if st.button("Exit Guest Mode"):
                st.session_state.user_session = None
                st.rerun()

# --- MAIN: ONBOARDING ---
# If logged in but no profile (Course/Role), show setup
if st.session_state.user_session and st.session_state.user_session != "GUEST" and not st.session_state.profile:
    st.header("📝 Complete your Profile")
    
    role = st.selectbox("I am a:", ["student", "teacher"])
    course = st.text_input("Course Name (e.g. Computer Science)")
    level = st.text_input("Level (e.g. Bachelor)")
    
    if st.button("Save Profile"):
        user_id = st.session_state.user_session.user.id
        profile_data = {
            "id": user_id,
            "role": role,
            "course": course,
            "level": level,
            "is_guest": False
        }
        supabase.table("profiles").upsert(profile_data).execute()
        st.session_state.profile = profile_data
        st.rerun()

# --- MAIN: CHAT INTERFACE ---
elif st.session_state.user_session:
    st.header("💬 Chat with Student AI")

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a question about your course..."):
        # Add User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare Payload
        is_guest = st.session_state.user_session == "GUEST"
        user_id = "GUEST" if is_guest else st.session_state.user_session.user.id
        
        role = "student"
        course = "General"
        level = "Basic"
        
        if not is_guest and st.session_state.profile:
            role = st.session_state.profile.get('role', 'student')
            course = st.session_state.profile.get('course', 'General')
            level = st.session_state.profile.get('level', 'Basic')

        payload = {
            "user_id": user_id,
            "query": prompt,
            "role": role,
            "course": course,
            "level": level
        }

        # Call Backend API
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                response = requests.post(f"{API_URL}/chat", json=payload)
                if response.status_code == 200:
                    ai_response = response.json().get("answer", "No response.")
                    message_placeholder.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    error_msg = "Error connecting to AI Brain."
                    message_placeholder.error(error_msg)
            except Exception as e:
                message_placeholder.error("Backend unreachable. Is it running?")