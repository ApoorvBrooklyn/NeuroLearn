import streamlit as st
import json
from datetime import datetime

# Check if user is logged in
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

def load_test(test_id):
    try:
        with open('tests.json', 'r') as f:
            tests = json.load(f)
            # Find the test with matching id
            for test in tests:
                if test['id'] == test_id:
                    return test
            return None
    except FileNotFoundError:
        return None

def save_submission(submission):
    try:
        with open('submissions.json', 'r') as f:
            submissions = json.load(f)
    except FileNotFoundError:
        submissions = []
    
    submissions.append(submission)
    with open('submissions.json', 'w') as f:
        json.dump(submissions, f)

def test_interface():
    st.title("Test Interface")

    if 'current_test' not in st.session_state:
        # Show available tests
        try:
            with open('tests.json', 'r') as f:
                tests = json.load(f)
                if not tests:  # Check if tests list is empty
                    st.warning("No tests available")
                    return
                
                # Create a list of test names with their IDs
                test_options = [f"{test['name']} - {test['subject']}" for test in tests]
                selected_index = st.selectbox("Select Test", range(len(test_options)), format_func=lambda x: test_options[x])
                
                if st.button("Start Test"):
                    st.session_state.current_test = tests[selected_index]['id']
                    st.rerun()
        except FileNotFoundError:
            st.error("No tests available")
            return
        except json.JSONDecodeError:
            st.error("Invalid test data format")
            return
    else:
        # Show current test
        test = load_test(st.session_state.current_test)
        if not test:
            st.error("Test not found")
            return
        
        st.header(f"{test['name']} - {test['subject']}")
        st.write(f"Duration: {test['duration']} minutes")
        st.write(f"Total Marks: {test['total_marks']}")
        
        # Initialize answers in session state
        if 'answers' not in st.session_state:
            st.session_state.answers = {}
        
        # Display questions
        for i, question in enumerate(test['questions']):
            st.subheader(f"Question {i+1} ({question['marks']} marks)")
            st.write(question['question'])
            st.write(f"Type: {question['type']}")
            
            if question['type'] == 'Short Answer':
                answer = st.text_area("Your answer:", key=f"q_{i}")
            else:  # Multiple Choice or True/False
                answer = st.radio(
                    "Select your answer:",
                    question['options'],
                    key=f"q_{i}"
                )
            st.session_state.answers[f"q_{i}"] = answer
        
        col1, col2 = st.columns(2)
        # Submit button
        if col1.button("Submit Test"):
            submission = {
                'student': st.session_state.username,
                'test_id': st.session_state.current_test,
                'test_name': test['name'],
                'answers': st.session_state.answers,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'id': f"sub_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            save_submission(submission)
            st.success("Test submitted successfully!")
            
            # Clear test state
            del st.session_state.current_test
            del st.session_state.answers
        
        # Return to dashboard
        if col2.button("Return to Dashboard"):
            st.switch_page("pages/student_dashboard.py")

if __name__ == "__main__":
    test_interface()