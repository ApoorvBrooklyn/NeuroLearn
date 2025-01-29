import streamlit as st
import json
from datetime import datetime

# Check if user is logged in
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

def load_content(content_type):
    try:
        with open(f'{content_type}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def student_dashboard():
    st.title(f"Welcome, {st.session_state.username}!")
    
    # Sidebar navigation
    selection = st.sidebar.selectbox(
        "Choose Activity",
        ["Dashboard", "Take Test", "View Notes", "My Submissions", "View Grades"]
    )
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.switch_page("app.py")
    
    if selection == "Dashboard":
        st.header("Your Dashboard")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Tests")
            tests = load_content('tests')
            if tests:
                for test in tests:
                    if st.button(f"Take {test['name']}", key=test['name']):
                        st.switch_page("pages/test_interface.py")
            else:
                st.info("No tests available")
        
        with col2:
            st.subheader("Study Materials")
            notes = load_content('notes')
            if notes:
                for note in notes:
                    st.write(f"📚 {note['title']}")
            else:
                st.info("No study materials available")
    
    elif selection == "Take Test":
        st.switch_page("pages/test_interface.py")
    
    elif selection == "View Notes":
        st.header("Study Materials")
        notes = load_content('notes')
        if notes:
            for note in notes:
                with st.expander(note['title']):
                    st.write(note['content'])
                    st.download_button(
                        "Download PDF",
                        note['file'],
                        file_name=f"{note['title']}.pdf"
                    )
        else:
            st.info("No study materials available")
    
    elif selection == "My Submissions":
        st.header("Your Submissions")
        submissions = load_content('submissions')
        if submissions:
            for sub in submissions:
                st.write(f"Test: {sub['test_name']}")
                st.write(f"Score: {sub['score']}")
                st.write(f"Submitted: {sub['date']}")
                st.divider()
        else:
            st.info("No submissions yet")
    
    elif selection == "View Grades":
        st.header("Your Grades")
        grades = load_content('grades')
        if grades:
            for grade in grades:
                st.metric(grade['subject'], f"{grade['score']}%")
        else:
            st.info("No grades available")

if __name__ == "__main__":
    student_dashboard()