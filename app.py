# import streamlit as st
# import json
# import hashlib
# from datetime import datetime
# import os

# # Initialize session states
# if 'active_tab' not in st.session_state:
#     st.session_state.active_tab = 'login'
# if 'logged_in' not in st.session_state:
#     st.session_state.logged_in = False
# if 'username' not in st.session_state:
#     st.session_state.username = None
# if 'user_type' not in st.session_state:
#     st.session_state.user_type = None

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def load_users():
#     if not os.path.exists('users.json'):
#         with open('users.json', 'w') as f:
#             json.dump({'professors': {}, 'students': {}}, f)
#     with open('users.json', 'r') as f:
#         return json.load(f)

# def save_users(users):
#     with open('users.json', 'w') as f:
#         json.dump(users, f)

# def register_user(username, password, user_type, email):
#     users = load_users()
#     user_category = 'professors' if user_type == 'Professor' else 'students'
    
#     if username in users[user_category]:
#         return False, "Username already exists"
    
#     users[user_category][username] = {
#         'password': hash_password(password),
#         'email': email,
#         'created_at': datetime.now().isoformat(),
#         'last_login': None
#     }
#     save_users(users)
#     return True, "Registration successful"

# def authenticate_user(username, password, user_type):
#     users = load_users()
#     user_category = 'professors' if user_type == 'Professor' else 'students'
    
#     if username not in users[user_category]:
#         return False, "Invalid username"
    
#     if users[user_category][username]['password'] != hash_password(password):
#         return False, "Invalid password"
    
#     users[user_category][username]['last_login'] = datetime.now().isoformat()
#     save_users(users)
#     return True, "Login successful"

# # Handle tab switching
# def switch_tab(tab_name):
#     st.session_state.active_tab = tab_name

# # Add tab buttons with click handlers
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("Login", key="login_tab"):
#         switch_tab('login')
# with col2:
#     if st.button("Register", key="register_tab"):
#         switch_tab('register')

# # Registration Form
# if st.session_state.active_tab == 'register':
#     with st.container():
#         st.markdown('<div class="form-container">', unsafe_allow_html=True)
#         st.markdown("""
#             <div class="welcome-message">
#                 <h4 style="margin: 0;">✨ Create Account</h4>
#                 <p style="margin: 0.5rem 0 0 0;">Join our educational community today!</p>
#             </div>
#         """, unsafe_allow_html=True)
        
#         reg_user_type = st.selectbox("👤 Register as", ["Student", "Professor"])
#         reg_username = st.text_input("👤 Username", key="reg_username")
#         reg_email = st.text_input("📧 Email", key="reg_email")
#         reg_password = st.text_input("🔑 Password", type="password", key="reg_password")
#         reg_confirm_password = st.text_input("🔑 Confirm Password", type="password", key="reg_confirm")
        
#         if st.button("Register", key="register_button"):
#             if not all([reg_username, reg_email, reg_password, reg_confirm_password]):
#                 st.error("Please fill in all fields")
#             elif reg_password != reg_confirm_password:
#                 st.error("Passwords do not match")
#             else:
#                 success, message = register_user(reg_username, reg_password, reg_user_type, reg_email)
#                 if success:
#                     st.success(message)
#                     switch_tab('login')
#                 else:
#                     st.error(message)

# # Login Form
# if st.session_state.active_tab == 'login':
#     with st.container():
#         st.markdown('<div class="form-container">', unsafe_allow_html=True)
#         st.markdown("""
#             <div class="welcome-message">
#                 <h4 style="margin: 0;">👋 Welcome back!</h4>
#                 <p style="margin: 0.5rem 0 0 0;">Please login with your credentials</p>
#             </div>
#         """, unsafe_allow_html=True)
        
#         username = st.text_input("📧 Username", key="login_username")
#         password = st.text_input("🔑 Password", type="password", key="login_password")
#         user_type = st.selectbox("👤 Login as", ["Student", "Professor"], key="login_user_type")
        
#         if st.button("Login", key="login_button"):
#             if not username or not password:
#                 st.error("Please fill in all fields")
#             else:
#                 success, message = authenticate_user(username, password, user_type)
#                 if success:
#                     st.session_state.logged_in = True
#                     st.session_state.username = username
#                     st.session_state.user_type = user_type
#                     st.success(message)
                    
#                     # Redirect based on user type
#                     if user_type == "Student":
#                         st.switch_page("pages/student_dashboard.py")
#                     else:
#                         st.switch_page("pages/professor_dashboard.py")
#                 else:
#                     st.error(message)                           




import streamlit as st
import json
import hashlib
from datetime import datetime
import os

# Custom CSS for styling
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background-color: #f5f7fb;
    }
    
    /* Form container styling */
    .form-container {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 2rem auto;
        max-width: 450px;
    }
    
    /* Welcome message styling */
    .welcome-message {
        text-align: center;
        margin-bottom: 2rem;
        color: #1f1f1f;
    }
    
    .welcome-message h4 {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .welcome-message p {
        color: #666;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 500;
        margin-top: 1rem;
        transition: background-color 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #2563eb;
    }
    
    /* Tab button styling */
    div.row-widget.stHorizontal > div[data-testid="stHorizontalBlock"] {
        background-color: white;
        border-radius: 10px;
        padding: 0.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 5px;
        border: 1px solid #e2e8f0;
        padding: 0.5rem;
    }
    
    .stSelectbox > div > div > div {
        border-radius: 5px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session states
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'login'
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as f:
            json.dump({'professors': {}, 'students': {}}, f)
    with open('users.json', 'r') as f:
        return json.load(f)

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

def register_user(username, password, user_type, email):
    users = load_users()
    user_category = 'professors' if user_type == 'Professor' else 'students'
    
    if username in users[user_category]:
        return False, "Username already exists"
    
    users[user_category][username] = {
        'password': hash_password(password),
        'email': email,
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }
    save_users(users)
    return True, "Registration successful"

def authenticate_user(username, password, user_type):
    users = load_users()
    user_category = 'professors' if user_type == 'Professor' else 'students'
    
    if username not in users[user_category]:
        return False, "Invalid username"
    
    if users[user_category][username]['password'] != hash_password(password):
        return False, "Invalid password"
    
    users[user_category][username]['last_login'] = datetime.now().isoformat()
    save_users(users)
    return True, "Login successful"

# Handle tab switching
def switch_tab(tab_name):
    st.session_state.active_tab = tab_name

# Page title with centered styling
st.markdown("<h1 style='text-align: center; color: #1f1f1f; margin-bottom: 2rem;'>Learning Management System</h1>", unsafe_allow_html=True)

# Add tab buttons with click handlers
col1, col2 = st.columns(2)
with col1:
    if st.button("Login", key="login_tab"):
        switch_tab('login')
with col2:
    if st.button("Register", key="register_tab"):
        switch_tab('register')

# Registration Form
if st.session_state.active_tab == 'register':
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("""
            <div class="welcome-message">
                <h4>✨ Create Account</h4>
                <p>Join our educational community today!</p>
            </div>
        """, unsafe_allow_html=True)
        
        reg_user_type = st.selectbox("👤 Register as", ["Student", "Professor"])
        reg_username = st.text_input("👤 Username", key="reg_username")
        reg_email = st.text_input("📧 Email", key="reg_email")
        reg_password = st.text_input("🔑 Password", type="password", key="reg_password")
        reg_confirm_password = st.text_input("🔑 Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", key="register_button"):
            if not all([reg_username, reg_email, reg_password, reg_confirm_password]):
                st.error("Please fill in all fields")
            elif reg_password != reg_confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = register_user(reg_username, reg_password, reg_user_type, reg_email)
                if success:
                    st.success(message)
                    switch_tab('login')
                else:
                    st.error(message)

# Login Form
if st.session_state.active_tab == 'login':
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("""
            <div class="welcome-message">
                <h4>👋 Welcome back!</h4>
                <p>Please login with your credentials</p>
            </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("📧 Username", key="login_username")
        password = st.text_input("🔑 Password", type="password", key="login_password")
        user_type = st.selectbox("👤 Login as", ["Student", "Professor"], key="login_user_type")
        
        if st.button("Login", key="login_button"):
            if not username or not password:
                st.error("Please fill in all fields")
            else:
                success, message = authenticate_user(username, password, user_type)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_type = user_type
                    st.success(message)
                    
                    # Redirect based on user type
                    if user_type == "Student":
                        st.switch_page("pages/student_dashboard.py")
                    else:
                        st.switch_page("pages/professor_dashboard.py")
                else:
                    st.error(message)