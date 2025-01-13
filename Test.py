import streamlit as st
import pandas as pd
import json
from datetime import datetime
import hashlib
import streamlit.components.v1 as components

# Constants for admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_test' not in st.session_state:
    st.session_state.current_test = None
if 'test_submitted' not in st.session_state:
    st.session_state.test_submitted = False
if 'warnings' not in st.session_state:
    st.session_state.warnings = 0

# JavaScript code for screen monitoring
MONITOR_SCRIPT = """
<script>
let warningCount = 0;
let lastWarningTime = Date.now();

// Function to check if enough time has passed since last warning
function canIssueWarning() {
    const now = Date.now();
    if (now - lastWarningTime >= 1000) { // 1 second cooldown
        lastWarningTime = now;
        return true;
    }
    return false;
}

// Function to send warning to Streamlit
function sendWarning() {
    if (canIssueWarning()) {
        warningCount++;
        const element = document.getElementById('warningCount');
        element.innerText = warningCount;
        
        // Send the warning count to Python
        fetch('http://localhost:8501', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'warning_count': warningCount
            })
        }).catch(error => console.log('Error:', error));
    }
}

// Monitor tab visibility
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        sendWarning();
    }
});

// Monitor window focus
window.addEventListener('blur', function() {
    sendWarning();
});

// Create warning counter element
document.addEventListener('DOMContentLoaded', function() {
    const warningElement = document.createElement('div');
    warningElement.id = 'warningCount';
    warningElement.style.display = 'none';
    warningElement.innerText = '0';
    document.body.appendChild(warningElement);
});
</script>
<div id="monitor-container">
    <div id="warningCount" style="display: none;">0</div>
</div>
"""

def initialize_monitoring():
    components.html(MONITOR_SCRIPT, height=0)
    
    # Simulate warning detection (for development)
    if st.session_state.get('simulate_warning', False):
        st.session_state.warnings += 1
        st.session_state.simulate_warning = False
        
        if st.session_state.warnings >= 3:
            return True
    return False


def check_warnings():
    if st.session_state.warnings >= 3:
        # Log the violation
        violations = load_violations()
        violations[st.session_state.username] = {
            'test_name': st.session_state.current_test,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'reason': "Multiple tab/screen changes detected - Unfair means"
        }
        save_violations(violations)
        
        # Reset test state
        st.session_state.current_test = None
        st.session_state.test_submitted = True
        st.session_state.warnings = 0
        return True
    return False

def load_violations():
    try:
        with open('violations.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_violations(violations):
    with open('violations.json', 'w') as f:
        json.dump(violations, f)

# Function to load student data from JSON file
def load_students():
    try:
        with open('students.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Function to save student data to JSON file
def save_students(students):
    with open('students.json', 'w') as f:
        json.dump(students, f)

def load_tests():
    try:
        with open('tests.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Function to save tests to JSON file
def save_tests(tests):
    with open('tests.json', 'w') as f:
        json.dump(tests, f)

# Function to load scores from JSON file
def load_scores():
    try:
        with open('scores.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Function to save scores to JSON file
def save_scores(scores):
    with open('scores.json', 'w') as f:
        json.dump(scores, f)

# Function to verify admin credentials
def verify_admin(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def login_page():
    st.title("MCQ Test Platform - Login")
    
    user_type = st.selectbox("Login as", ["Student", "Admin"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if user_type == "Admin":
            if verify_admin(username, password):
                st.session_state.user_type = "admin"
                st.session_state.logged_in = True
                st.success("Successfully logged in as Admin")
                st.rerun()
            else:
                st.error("Invalid admin credentials")
        else:
            students = load_students()
            if username in students:
                stored_password = students[username]['password']
                if stored_password == hashlib.sha256(password.encode()).hexdigest():
                    st.session_state.user_type = "student"
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Successfully logged in as Student")
                    st.rerun()
                else:
                    st.error("Invalid password")
            else:
                st.error("Student not found")
    
    # Student Registration (only shown when Student is selected)
    if user_type == "Student":
        st.markdown("---")
        st.subheader("New Student Registration")
        reg_username = st.text_input("New Username", key="reg_username")
        reg_password = st.text_input("New Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if not reg_username or not reg_password:
                st.error("Please fill in all fields")
            elif reg_password != confirm_password:
                st.error("Passwords do not match")
            else:
                students = load_students()
                if reg_username in students:
                    st.error("Username already exists")
                else:
                    students[reg_username] = {
                        'password': hashlib.sha256(reg_password.encode()).hexdigest(),
                        'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_students(students)
                    st.success("Registration successful! You can now login.")

def admin_page():
    st.title("Admin Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["Upload Test", "View Scores", "View Violations"])
    
    with tab1:
        st.header("Upload New Test")
        test_name = st.text_input("Test Name")
        duration = st.number_input("Test Duration (minutes)", min_value=1, value=30)
        
        questions = []
        num_questions = st.number_input("Number of Questions", min_value=1, value=1)
        
        for i in range(int(num_questions)):
            st.subheader(f"Question {i+1}")
            question = st.text_input(f"Question", key=f"q{i}")
            options = []
            for j in range(4):
                option = st.text_input(f"Option {j+1}", key=f"q{i}o{j}")
                options.append(option)
            correct_answer = st.selectbox(f"Correct Answer", options, key=f"q{i}a")
            
            if question and all(options) and correct_answer:
                questions.append({
                    'question': question,
                    'options': options,
                    'correct_answer': correct_answer
                })
        
        if st.button("Upload Test"):
            if test_name and questions and len(questions) == num_questions:
                tests = load_tests()
                tests[test_name] = {
                    'questions': questions,
                    'duration': duration
                }
                save_tests(tests)
                st.success("Test uploaded successfully!")
            else:
                st.error("Please fill all the fields")
    
    with tab2:
        st.header("Student Scores")
        scores = load_scores()
        if scores:
            df = pd.DataFrame(scores).T
            st.dataframe(df)
        else:
            st.info("No test scores available")
    
    with tab3:
        st.header("Test Violations")
        violations = load_violations()
        if violations:
            df = pd.DataFrame(violations).T
            st.dataframe(df)
        else:
            st.info("No violations recorded")

def student_page():
    st.title("Student Dashboard")
    
    if not st.session_state.current_test and not st.session_state.test_submitted:
        st.header("Available Tests")
        tests = load_tests()
        if tests:
            test_name = st.selectbox("Select Test", list(tests.keys()))
            if st.button("Start Test"):
                st.session_state.current_test = test_name
                st.session_state.start_time = datetime.now()
                st.session_state.warnings = 0
                st.rerun()
        else:
            st.info("No tests available")
    
    elif st.session_state.current_test and not st.session_state.test_submitted:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.header(f"Test: {st.session_state.current_test}")
        
        with col2:
            # Debug button (remove in production)
            if st.button("Simulate Tab Switch"):
                st.session_state.simulate_warning = True
                st.rerun()
        
        # Initialize monitoring
        should_terminate = initialize_monitoring()
        
        # Show warning count
        if st.session_state.warnings > 0:
            st.warning(f"⚠️ Warning {st.session_state.warnings}/3: Tab switching detected!")
            
            if st.session_state.warnings >= 3:
                st.error("⚠️ Test terminated due to multiple violations. This incident has been reported.")
                
                # Log violation
                violations = load_violations()
                violations[st.session_state.username] = {
                    'test_name': st.session_state.current_test,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'reason': f"Multiple tab changes detected ({st.session_state.warnings} warnings) - Unfair means"
                }
                save_violations(violations)
                
                st.session_state.current_test = None
                st.session_state.test_submitted = True
                st.rerun()
                return
        
        # Display test content
        tests = load_tests()
        test = tests[st.session_state.current_test]
        
        # Calculate remaining time
        elapsed_time = (datetime.now() - st.session_state.start_time).total_seconds()
        remaining_time = max(0, test['duration'] * 60 - elapsed_time)
        
        st.write(f"Time remaining: {int(remaining_time/60)}:{int(remaining_time%60):02d}")
        
        if remaining_time <= 0:
            st.warning("Time's up! Please submit your answers.")
        answers = {}
        for i, q in enumerate(test['questions']):
            st.subheader(f"Question {i+1}")
            st.write(q['question'])
            answer = st.radio("Select your answer:", q['options'], key=f"q{i}")
            answers[f"q{i}"] = {'question': q['question'], 'answer': answer, 'correct': q['correct_answer']}
        
        if st.button("Submit Test") or remaining_time <= 0:
            score = sum(1 for q in answers.values() if q['answer'] == q['correct'])
            total_questions = len(test['questions'])
            percentage = (score / total_questions) * 100
            
            scores = load_scores()
            scores[st.session_state.username] = {
                'test_name': st.session_state.current_test,
                'score': score,
                'total': total_questions,
                'percentage': percentage,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'warnings_received': st.session_state.warnings
            }
            save_scores(scores)
            
            st.session_state.test_submitted = True
            st.session_state.final_answers = answers
            st.rerun()
        
        
    

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.current_test = None
            st.session_state.test_submitted = False
            st.rerun()
        
        if st.session_state.user_type == "admin":
            admin_page()
        else:
            student_page()

if __name__ == "__main__":
    main()