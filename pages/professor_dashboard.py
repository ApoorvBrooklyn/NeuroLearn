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

def save_content(content_type, data):
    with open(f'{content_type}.json', 'w') as f:
        json.dump(data, f)

def evaluate_test(submission):
    """
    Automatically evaluate test submission by comparing with correct answers
    Returns: (score, total_marks, feedback)
    """
    tests = load_content('tests')
    test = None
    # Find the corresponding test
    for t in tests:
        if t['id'] == submission['test_id']:
            test = t
            break
    
    if not test:
        return 0, 0, "Test not found"

    score = 0
    feedback = []
    total_marks = test['total_marks']
    
    for i, (question, answer) in enumerate(submission['answers'].items()):
        q_index = int(question.split('_')[1])  # Extract question index from 'q_0', 'q_1' etc.
        correct = test['questions'][q_index]['correct_answer']
        marks = test['questions'][q_index]['marks']
        
        if test['questions'][q_index]['type'] == 'Short Answer':
            # For short answers, check if key words from correct answer appear in student's answer
            keywords = correct.lower().split()
            student_answer = answer.lower()
            matches = sum(1 for keyword in keywords if keyword in student_answer)
            accuracy = matches / len(keywords)
            question_score = marks * accuracy
            score += question_score
            feedback.append(f"Q{q_index + 1}: {question_score}/{marks} marks - {accuracy*100:.0f}% keyword match")
        else:
            # For MCQ and True/False
            if answer == correct:
                score += marks
                feedback.append(f"Q{q_index + 1}: {marks}/{marks} marks - Correct")
            else:
                feedback.append(f"Q{q_index + 1}: 0/{marks} marks - Incorrect. Correct answer: {correct}")

    return score, total_marks, "\n".join(feedback)

def professor_dashboard():
    st.title(f"Welcome, Professor {st.session_state.username}!")
    
    selection = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Create Test", "Upload Notes", "View Submissions", "View Statistics"]
    )
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.switch_page("app.py")
    
    submissions = load_content('submissions')
    if isinstance(submissions, dict):
        submissions_list = list(submissions.values())
    else:
        submissions_list = submissions
    
    if selection == "Dashboard":
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Activities")
            st.write("📝 Latest submissions")
            for sub in submissions_list[-5:]:
                st.write(f"Student: {sub['student']}")
                st.write(f"Test: {sub['test_name']}")
                if not sub.get('evaluated'):
                    st.write("Status: Pending evaluation")
                else:
                    st.write(f"Score: {sub['score']}/{sub['total_marks']}")
                st.divider()
        
        with col2:
            st.subheader("Quick Actions")
            if st.button("Create New Test"):
                st.switch_page("pages/test_creator.py")
            if st.button("Upload Study Material"):
                selection = "Upload Notes"
    
    elif selection == "Create Test":
        st.switch_page("pages/test_creator.py")
    
    elif selection == "Upload Notes":
        st.header("Upload Study Materials")
        title = st.text_input("Title")
        content = st.text_area("Content")
        file = st.file_uploader("Upload PDF", type=['pdf'])
        
        if st.button("Upload"):
            if title and (content or file):
                notes = load_content('notes')
                if isinstance(notes, dict):
                    notes = []
                notes.append({
                    'title': title,
                    'content': content,
                    'file': file.getvalue() if file else None,
                    'uploaded_by': st.session_state.username,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                save_content('notes', notes)
                st.success("Study material uploaded successfully!")
    
    elif selection == "View Submissions":
        st.header("View Submissions")
        if submissions_list:
            for sub in submissions_list:
                if not sub.get('evaluated'):
                    score, total_marks, feedback = evaluate_test(sub)
                    sub['score'] = score
                    sub['total_marks'] = total_marks
                    sub['feedback'] = feedback
                    sub['evaluated'] = True
                    save_content('submissions', submissions_list)
                
                with st.expander(f"Student: {sub['student']} - Test: {sub['test_name']}"):
                    st.write(f"Submitted: {sub['date']}")
                    st.write(f"Score: {sub['score']}/{sub['total_marks']} ({(sub['score']/sub['total_marks']*100):.1f}%)")
                    st.write("Feedback:")
                    st.code(sub['feedback'])
                    st.write("Detailed Answers:", sub['answers'])
    
    elif selection == "View Statistics":
        st.header("Class Statistics")
        if submissions_list:
            # Calculate statistics only for evaluated submissions
            evaluated_subs = [sub for sub in submissions_list if sub.get('evaluated')]
            if evaluated_subs:
                avg_score = sum(sub['score']/sub['total_marks']*100 for sub in evaluated_subs) / len(evaluated_subs)
                st.metric("Average Score", f"{avg_score:.1f}%")
                
                # Test-wise statistics
                st.subheader("Test-wise Performance")
                test_stats = {}
                for sub in evaluated_subs:
                    test_name = sub['test_name']
                    if test_name not in test_stats:
                        test_stats[test_name] = []
                    test_stats[test_name].append(sub['score']/sub['total_marks']*100)
                
                for test, scores in test_stats.items():
                    avg = sum(scores) / len(scores)
                    st.metric(test, f"{avg:.1f}%")
            else:
                st.info("No evaluated submissions available")
        else:
            st.info("No data available for statistics")

if __name__ == "__main__":
    professor_dashboard()