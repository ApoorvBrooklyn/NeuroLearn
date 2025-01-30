import streamlit as st
from streamlit.components.v1 import html

# Set page configuration
st.set_page_config(page_title="RV Meet", layout="wide")

# Custom CSS for improved design
st.markdown("""
    <style>
    /* Main layout and gradient styling */
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
    
    /* Content sections */
    .content-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Button styling */
    .action-button {
        background-color: #1e3c72;
        color: white;
        padding: 1rem 2rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        text-align: center;
        margin: 1rem;
        font-size: 1.2rem;
        transition: transform 0.3s ease;
        display: inline-block;
        text-decoration: none;
    }
    
    .action-button:hover {
        background-color: #2a5298;
        transform: translateY(-2px);
    }
    
    /* Logo styling */
    .college-logo {
        width: 80px;
        height: auto;
        margin-bottom: 1rem;
    }
    
    /* Meeting room styling */
    .meeting-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    iframe {
        border: none;
        border-radius: 8px;
        width: 100%;
        height: 600px;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 5px;
        border: 2px solid #1e3c72;
        padding: 0.5rem;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header section
st.markdown("""
    <div class="main-header">
        <img src="https://rvce.edu.in/sites/default/files/logo_new.png" class="college-logo">
        <div class="college-name">RV COLLEGE OF ENGINEERING</div>
        <div class="app-title">RV Meet</div>
        <div style="font-size: 1.1rem;">Virtual Meeting Platform</div>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'show_section' not in st.session_state:
    st.session_state.show_section = None

# Main content section
st.markdown('<div class="content-section">', unsafe_allow_html=True)

# Single set of buttons for both joining and hosting
col1, col2 = st.columns(2)
with col1:
    if st.button("🎥 Join Meeting", use_container_width=True):
        st.session_state.show_section = 'join'
with col2:
    if st.button("📡 Host Meeting", use_container_width=True):
        st.session_state.show_section = 'host'

# Meeting sections
if st.session_state.show_section == 'join':
    st.markdown("### Join a Meeting")
    meeting_id = st.text_input("Enter Meeting ID:", key="join_id")
    if st.button("Connect", key="join_button"):
        if meeting_id.strip():
            st.success(f"Joining meeting: {meeting_id}")
            st.markdown('<div class="meeting-container">', unsafe_allow_html=True)
            html(f"""
                <iframe
                    src="https://meet.jit.si/{meeting_id.strip()}"
                    allow="camera; microphone; fullscreen"
                    title="Meeting Room"
                ></iframe>
            """, height=600)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Please enter a valid Meeting ID!")

elif st.session_state.show_section == 'host':
    st.markdown("### Host a Meeting")
    meeting_id = st.text_input("Enter Meeting Name:", value="RVMeetRoom", key="host_id")
    if st.button("Start Meeting", key="host_button"):
        st.success(f"Hosting meeting: {meeting_id}")
        st.markdown('<div class="meeting-container">', unsafe_allow_html=True)
        html(f"""
            <iframe
                src="https://meet.jit.si/{meeting_id.strip()}"
                allow="camera; microphone; fullscreen"
                title="Meeting Room"
            ></iframe>
        """, height=600)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; color: #666;">
        <p style="font-size: 0.9rem;">
            © 2025 RV College of Engineering<br>
            Mysuru Road, RV Vidyaniketan Post, Bengaluru-560059
        </p>
    </div>
""", unsafe_allow_html=True)