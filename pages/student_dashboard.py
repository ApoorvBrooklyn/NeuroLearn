import streamlit as st
import json
from datetime import datetime
import os
import sys
from pathlib import Path
from pages.selfstudy import ConcentrationDetector

# Add parent directory to path to allow imports from sibling directories
sys.path.append(str(Path(__file__).parent.parent))

# Check if user is logged in
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

def load_content(content_type):
    try:
        file_path = Path(__file__).parent.parent / f'{content_type}.json'
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_study_session(username, report):
    """Save study session report to JSON file"""
    file_path = Path(__file__).parent.parent / 'study_sessions.json'
    try:
        with open(file_path, 'r') as f:
            sessions = json.load(f)
    except FileNotFoundError:
        sessions = {}
    
    if username not in sessions:
        sessions[username] = []
    
    sessions[username].append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'report': report
    })
    
    with open(file_path, 'w') as f:
        json.dump(sessions, f)

def handle_study_session(duration):
    """Handle the study session and return the report"""
    try:
        detector = ConcentrationDetector(duration_minutes=duration)
        with st.spinner("Study session in progress..."):
            report = detector.process_video_feed()
            
            if report:
                save_study_session(st.session_state.username, report)
                return report
            return None
    except Exception as e:
        st.error(f"Error during study session: {str(e)}")
        return None

def display_study_history():
    """Display previous study sessions"""
    file_path = Path(__file__).parent.parent / 'study_sessions.json'
    try:
        with open(file_path, 'r') as f:
            sessions = json.load(f)
            user_sessions = sessions.get(st.session_state.username, [])
            
            if user_sessions:
                for session in reversed(user_sessions):
                    with st.expander(f"Study Session - {session['timestamp']}"):
                        report = session['report']
                        st.write(f"Total Study Time: {report['total_time']:.2f} seconds")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Concentration Levels")
                            for level, data in report['concentration_levels'].items():
                                st.write(f"{level}: {data['time']:.2f}s ({data['percentage']:.1f}%)")
                        
                        with col2:
                            st.subheader("Working Status")
                            for status, data in report['working_status'].items():
                                st.write(f"{status}: {data['time']:.2f}s ({data['percentage']:.1f}%)")
            else:
                st.info("No study sessions recorded yet")
    except FileNotFoundError:
        st.info("No study sessions recorded yet")

def student_dashboard():
    st.title(f"Welcome, {st.session_state.username}!")
    
    # Sidebar navigation with added Social Connect option
    selection = st.sidebar.selectbox(
        "Choose Activity",
        ["Dashboard", "Self Study", "Take Test", "View Notes", "My Submissions", "View Grades", "Social Connect", "Create a Meet"]
    )
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.switch_page("app.py")
    
    # Handle Social Connect selection
    if selection == "Social Connect":
        st.switch_page("pages/social_connect.py")
        return
    
    if selection == "Create a Meet":
        st.switch_page("pages/meet.py")
        return
    
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
        
        st.subheader("Recent Study Sessions")
        display_study_history()
    
    elif selection == "Self Study":
        st.header("Self Study Session")
        st.write("Monitor your concentration during study sessions")
        
        duration = st.number_input(
            "Study session duration (minutes)", 
            min_value=1, 
            max_value=120, 
            value=30
        )
        
        if st.button("Start Study Session"):
            report = handle_study_session(duration)
            
            if report:
                st.success("Study session completed!")
                st.subheader("Session Report")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Concentration Levels:")
                    for level, data in report['concentration_levels'].items():
                        st.write(f"{level}: {data['time']:.1f}s ({data['percentage']:.1f}%)")
                
                with col2:
                    st.write("Working Status:")
                    for status, data in report['working_status'].items():
                        st.write(f"{status}: {data['time']:.1f}s ({data['percentage']:.1f}%)")

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