import streamlit as st
import json
from datetime import datetime
import uuid

def load_content(content_type):
    try:
        with open(f'{content_type}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_content(content_type, data):
    with open(f'{content_type}.json', 'w') as f:
        json.dump(data, f)

def test_creator():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.switch_page("app.py")

    st.title("Create New Test")

    # Test basic information
    test_name = st.text_input("Test Name")
    subject = st.text_input("Subject")
    duration = st.number_input("Duration (minutes)", min_value=1, value=60)
    total_marks = st.number_input("Total Marks", min_value=1, value=100)
    
    # Question creation section
    st.subheader("Add Questions")
    
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    
    # Add new question
    with st.expander("Add New Question"):
        question_type = st.selectbox(
            "Question Type",
            ["Multiple Choice", "True/False", "Short Answer"],
            key="new_q_type"
        )
        
        question_text = st.text_area("Question Text", key="new_q_text")
        marks = st.number_input("Marks", min_value=1, value=1, key="new_q_marks")
        
        if question_type == "Multiple Choice":
            options = []
            for i in range(4):
                option = st.text_input(f"Option {i+1}", key=f"option_{i}")
                options.append(option)
            correct_answer = st.selectbox("Correct Answer", options, key="correct_ans")
        
        elif question_type == "True/False":
            correct_answer = st.selectbox("Correct Answer", ["True", "False"], key="tf_ans")
            options = ["True", "False"]
        
        else:  # Short Answer
            correct_answer = st.text_area("Model Answer", key="sa_ans")
            options = []
        
        if st.button("Add Question"):
            if question_text:
                new_question = {
                    "id": str(uuid.uuid4()),
                    "type": question_type,
                    "question": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                    "marks": marks
                }
                st.session_state.questions.append(new_question)
                st.success("Question added successfully!")
                st.rerun()

    # Display and edit existing questions
    st.subheader("Current Questions")
    total_test_marks = 0
    
    for i, q in enumerate(st.session_state.questions):
        total_test_marks += q['marks']
        with st.expander(f"Question {i+1}: {q['question'][:50]}..."):
            st.write(f"Type: {q['type']}")
            st.write(f"Marks: {q['marks']}")
            if q['options']:
                st.write("Options:")
                for opt in q['options']:
                    st.write(f"- {opt}")
            st.write(f"Correct Answer: {q['correct_answer']}")
            
            if st.button(f"Delete Question {i+1}"):
                st.session_state.questions.pop(i)
                st.rerun()

    st.write(f"Total marks in questions: {total_test_marks}/{total_marks}")

    # Save test
    if st.button("Save Test"):
        if not test_name:
            st.error("Please provide a test name")
            return
        
        if not st.session_state.questions:
            st.error("Please add at least one question")
            return
        
        if total_test_marks != total_marks:
            st.error(f"Total marks in questions ({total_test_marks}) does not match specified total marks ({total_marks})")
            return
        
        test_data = {
            "id": str(uuid.uuid4()),
            "name": test_name,
            "subject": subject,
            "duration": duration,
            "total_marks": total_marks,
            "questions": st.session_state.questions,
            "created_by": st.session_state.username,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        tests = load_content('tests')
        tests.append(test_data)
        save_content('tests', tests)
        
        st.success("Test created successfully!")
        st.session_state.questions = []  # Clear questions after saving
        st.rerun()

    if st.button("Back to Dashboard"):
        st.switch_page("pages/professor_dashboard.py")

if __name__ == "__main__":
    test_creator()