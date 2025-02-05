import streamlit as st
from streamlit.components.v1 import html
from PIL import Image
import os

st.set_page_config(page_title="Connectify", layout="wide")

# Initialize the session state for registered professors if not already set
if 'registered_professors' not in st.session_state:
    st.session_state.registered_professors = ["professor123", "professor456", "professor789"]

logo_path = r"logo.jpeg"

if os.path.exists(logo_path):
    logo_image = Image.open(logo_path)
else:
    logo_image = None
    st.error("⚠️ Logo image not found! Please check the path.")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; font-family: 'Arial', sans-serif; }
    .sidebar .sidebar-content { background-color: #34495e; color: white; }
    .sidebar .sidebar-content a { color: #ecf0f1; }
    h1 { color: #2980b9; font-size: 2.5em; font-weight: 700; }
    h2 { color: #2980b9; font-size: 1.8em; font-weight: 600; }
    .sidebar h2 { font-size: 1.3em; margin-bottom: 10px; }
    .button { display: block; width: 100%; margin: 10px 0; padding: 12px;
              background-color: #2980b9; color: white; border: none;
              border-radius: 8px; text-align: center; font-size: 16px;
              transition: background-color 0.3s ease; }
    .button:hover { background-color: #3498db; }
    .button:active { background-color: #1f77b4; }
    .icon { color: #2980b9; margin-right: 8px; }
    .logo { vertical-align: middle; margin-right: 10px; }
    .title { font-size: 2.5em; font-weight: 700; color: #2980b9;
             display: inline; vertical-align: middle; }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 5]) 

with col1:
    if logo_image:
        st.image(logo_image, width=70, use_container_width=False)

with col2:
    st.markdown("""<div style="display: flex; align-items: center; height: 100%;">  
                    <span class="title">Connectify - Your Meeting Hub</span>
                   </div>""", unsafe_allow_html=True)

st.subheader("Welcome to Connectify! 🚀")
st.write("""*"The best way to predict the future is to create it." – Abraham Lincoln*  
           Ready to connect and collaborate?  
           Host or join a meeting seamlessly with Connectify.""")

menu = st.radio("Choose an option:", ["📡 Join Meeting", "🎥 Host Meeting", "✍️ Register as Professor"])

if menu == "📡 Join Meeting":
    st.subheader("Join a Meeting")
    meeting_id = st.text_input("🔑 Enter Meeting ID:")
    if st.button("Join Meeting", key="join"):
        if meeting_id.strip():
            meeting_link = f"https://meet.jit.si/{meeting_id.strip()}#config.lobbyMode=true"
            st.success(f"Joining meeting: *{meeting_id}*")
            st.markdown(f"### [Click here to join the meeting in a new tab 🚀]({meeting_link})", unsafe_allow_html=True)
        else:
            st.error("Please enter a valid Meeting ID!")

elif menu == "🎥 Host Meeting":
    st.subheader("Host a New Meeting")
    user_id = st.text_input("🔑 Enter your Registered ID (Professor ID):")
    
    if user_id.strip():
        if user_id.strip() in st.session_state.registered_professors:
            meeting_id = st.text_input("🔑 Enter a unique Meeting Name (or leave blank for default):", value="MyMeetingRoom")
            if st.button("Generate Meeting Link", key="host"):
                meeting_link = f"https://meet.jit.si/{meeting_id.strip()}#config.lobbyMode=true&userInfo.displayName='Professor'"
                st.success(f"Hosting a meeting: *{meeting_id}*")
                st.markdown(f"### [Click here to open the meeting in a new tab 🚀]({meeting_link})", unsafe_allow_html=True)
        else:
            st.error("⚠️ You are not authorized to host a meeting. Only registered professors can host meetings.")
    else:
        st.warning("Please enter your Professor ID to host a meeting.")

elif menu == "✍️ Register as Professor":
    st.subheader("Professor Registration")
    name = st.text_input("🔑 Enter your full name:")
    email = st.text_input("✉️ Enter your email:")
    professor_id = st.text_input("🔑 Create a Professor ID (unique):")
    
    if st.button("Register", key="register"):
        if name.strip() and email.strip() and professor_id.strip():
            if not email.endswith(".prof@rvce.edu.in"):
                st.error("⚠️ Email must end with '.prof@rvce.edu.in'")
            elif professor_id.strip() not in st.session_state.registered_professors:
                # Register the professor
                st.session_state.registered_professors.append(professor_id.strip())
                st.success(f"🎉 Registration successful! Welcome, Professor {name}. You can now host meetings.")
            else:
                st.error("⚠️ This ID is already registered.")
        else:
            st.error("⚠️ Please fill in all the fields.")
