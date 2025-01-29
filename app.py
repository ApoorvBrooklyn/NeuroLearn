import streamlit as st
import json
import hashlib
from datetime import datetime
import subprocess
import os

# Initialize session state
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
        return {
            'professors': {},
            'students': {}
        }

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

def login_page():
    st.title("Educational Platform - Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        user_type = st.selectbox("Login as", ["Student", "Professor"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users = load_users()
            user_category = 'students' if user_type.lower() == 'student' else 'professors'
            
            if username in users[user_category]:
                stored_password = users[user_category][username]['password']
                if stored_password == hashlib.sha256(password.encode()).hexdigest():
                    st.session_state.user_type = user_type.lower()
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Successfully logged in as {user_type}")
                    
                    # Redirect to appropriate dashboard
                    if user_type.lower() == 'student':
                        st.switch_page("pages/student_dashboard.py")
                    else:
                        st.switch_page("pages/professor_dashboard.py")
                else:
                    st.error("Invalid password")
            else:
                st.error(f"{user_type} not found")
    
    with tab2:
        st.header("Register")
        reg_user_type = st.selectbox("Register as", ["Student", "Professor"])
        reg_username = st.text_input("New Username")
        reg_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if not reg_username or not reg_password:
                st.error("Please fill in all fields")
            elif reg_password != confirm_password:
                st.error("Passwords do not match")
            else:
                users = load_users()
                user_category = 'students' if reg_user_type.lower() == 'student' else 'professors'
                
                if reg_username in users[user_category]:
                    st.error("Username already exists")
                else:
                    users[user_category][reg_username] = {
                        'password': hashlib.sha256(reg_password.encode()).hexdigest(),
                        'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_users(users)
                    st.success("Registration successful! You can now login.")

def main():
    if not st.session_state.logged_in:
        login_page()

if __name__ == "__main__":
    main()