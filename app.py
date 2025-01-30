import streamlit as st
import json
import hashlib
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Educational Platform",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS with modern design and fixed alignments
st.markdown("""
    <style>
    /* Main Container Styles */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
    }
    
    /* Stats Container */
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 2rem auto;
        max-width: 800px;
        flex-wrap: wrap;
    }
    
    .stat-item {
        text-align: center;
        padding: 1.5rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        min-width: 180px;
        margin: 0.5rem;
    }
    
    .stat-item h3 {
        margin: 0;
        font-size: 1.8rem;
        color: #1e3c72;
    }
    
    .stat-item p {
        margin: 0.5rem 0 0 0;
        color: #666;
    }
    
    /* Tab Container */
    .tab-container {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .tab-button {
        padding: 0.8rem 2rem;
        background: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        color: #1e3c72;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .tab-button.active {
        background: #1e3c72;
        color: white;
    }
    
    .tab-button:hover {
        transform: translateY(-2px);
    }
    
    /* Form Container */
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        max-width: 500px;
        margin: 1rem auto;
    }
    
    .welcome-message {
        border-left: 4px solid #1e3c72;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 4px;
        margin-bottom: 1.5rem;
    }
    
    /* Input Field Styles */
    .stTextInput > div > div {
        background-color: white;
        border-radius: 5px;
        border: 2px solid #e0e0e0;
        padding: 0.5rem;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: #1e3c72;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(30,60,114,0.3);
    }
    
    /* Hide empty elements */
    .stMarkdown:empty {
        display: none;
    }
    
    /* Footer Styles */
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 2rem;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .college-name {
        font-size: 1.2rem;
        color: #f0f0f0;
        margin-bottom: 0.5rem;
    }
    .app-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .welcome-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .role-selector {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .continue-btn {
        background-color: #1e3c72;
        color: white;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        text-align: center;
        margin-top: 1rem;
    }
    .continue-btn:hover {
        background-color: #2a5298;
    }
    .college-logo {
        width: 100px;
        height: 100px;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <img src="https://rvce.edu.in/sites/default/files/logo_new.png" class="college-logo">
        <div class="college-name">RV COLLEGE OF ENGINEERING</div>
        <div class="app-title">🌟 RV EDU CONNECT</div>
        <div style="font-size: 1.1rem;">Go Change The World</div>
        <div style="font-size: 1.1rem;">Connecting Minds, Bridging Communities</div>
    </div>
""", unsafe_allow_html=True)


logo_url = "https://rvce.edu.in/sites/default/files/logo_new.png"


# Initialize session state
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'login'

# Tab buttons
st.markdown("""
    <div class="tab-container">
        <button class="tab-button active" onclick="handleTabClick('login')">🔐 Login</button>
        <button class="tab-button" onclick="handleTabClick('register')">✍️ Register</button>
    </div>
""", unsafe_allow_html=True)

# Login Form
with st.container():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.markdown("""
        <div class="welcome-message">
            <h4 style="margin: 0;">👋 Welcome back!</h4>
            <p style="margin: 0.5rem 0 0 0;">Please login with your credentials to access your dashboard.</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_type = st.selectbox("👤 Login as", ["Student", "Professor"])
    username = st.text_input("📧 Username")
    password = st.text_input("🔑 Password", type="password")
    
    remember_me = st.checkbox("Remember me")
    
    if st.button("Login"):
        # Your existing login logic here
        pass
    
    st.markdown("""
        <div style="text-align: center; margin-top: 1rem;">
            <a href="#" style="color: #1e3c72; text-decoration: none;">Forgot Password?</a>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class="footer">
        <p>© 2025 Educational Platform. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state for user management
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'professors': {}, 'students': {}}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)