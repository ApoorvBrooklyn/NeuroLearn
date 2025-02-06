import streamlit as st
import json
from datetime import datetime
import base64
import os

# Check if user is logged in
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

def load_content(content_type):
    """
    Load content from JSON file with proper error handling
    """
    try:
        # Create file if it doesn't exist
        if not os.path.exists(f'{content_type}.json'):
            with open(f'{content_type}.json', 'w') as f:
                json.dump([], f)
        
        with open(f'{content_type}.json', 'r') as f:
            content = f.read()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_content(content_type, data):
    """
    Save content to JSON file with error handling
    """
    try:
        with open(f'{content_type}.json', 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

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
        q_index = int(question.split('_')[1])
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
    """
    Main dashboard function for professors
    """
    st.title(f"Welcome, Professor {st.session_state.username}!")
    
    # Initialize dashboard selection in session state
    if 'dashboard_selection' not in st.session_state:
        st.session_state.dashboard_selection = "Dashboard"
    
    # Sidebar navigation
    menu_options = ["Dashboard", "Create Test", "Upload Notes", "View Submissions", 
                   "View Statistics", "Create a meet"]
    selection = st.sidebar.selectbox(
        "Menu",
        menu_options,
        key="sidebar_selection",
        index=menu_options.index(st.session_state.dashboard_selection)
    )
    
    # Update session state
    st.session_state.dashboard_selection = selection
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.switch_page("app.py")
    
    # Handle page navigation
    if selection == "Create a Meet":
        st.switch_page("pages/meeting.py")
        return
    
    if selection == "Create Test":
        st.switch_page("pages/test_creator.py")
        return
    
    # Load submissions
    submissions = load_content('submissions')
    submissions_list = submissions if isinstance(submissions, list) else list(submissions.values())
    
    # Dashboard view
    if selection == "Dashboard":
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Activities")
            st.write("📝 Latest submissions")
            
            recent_submissions = submissions_list[-5:] if submissions_list else []
            if recent_submissions:
                for sub in recent_submissions:
                    with st.container():
                        st.write(f"Student: {sub['student']}")
                        st.write(f"Test: {sub['test_name']}")
                        if not sub.get('evaluated'):
                            st.write("Status: Pending evaluation")
                        else:
                            st.write(f"Score: {sub['score']}/{sub['total_marks']}")
                        st.divider()
            else:
                st.info("No recent submissions")
        
        with col2:
            st.subheader("Quick Actions")
            if st.button("Create New Test"):
                st.session_state.dashboard_selection = "Create Test"
                st.rerun()
            
            if st.button("Upload Study Material"):
                st.session_state.dashboard_selection = "Upload Notes"
                st.rerun()
    
    # Upload Notes view
    elif selection == "Upload Notes":
        st.header("Upload Study Materials")
        
        with st.form("upload_notes_form"):
            title = st.text_input("Title")
            content = st.text_area("Content")
            file = st.file_uploader("Upload PDF", type=['pdf'])
            
            submit_button = st.form_submit_button("Upload")
            
            if submit_button:
                if not title:
                    st.error("Please enter a title")
                elif not content and not file:
                    st.error("Please provide either content or upload a file")
                else:
                    try:
                        notes = load_content('notes')
                        
                        file_content = None
                        if file:
                            try:
                                file_content = base64.b64encode(file.getvalue()).decode('utf-8')
                            except Exception as e:
                                st.error(f"Error processing file: {str(e)}")
                                return
                        
                        new_note = {
                            'title': title,
                            'content': content,
                            'file': file_content,
                            'uploaded_by': st.session_state.username,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        notes.append(new_note)
                        save_content('notes', notes)
                        st.success("Study material uploaded successfully!")
                        st.session_state.dashboard_selection = "Dashboard"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving note: {str(e)}")
    
    # View Submissions view
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
        else:
            st.info("No submissions available")
    
    # View Statistics view
    elif selection == "View Statistics":
        st.header("Class Statistics")
        if submissions_list:
            evaluated_subs = [sub for sub in submissions_list if sub.get('evaluated')]
            if evaluated_subs:
                # Calculate overall statistics
                avg_score = sum(sub['score']/sub['total_marks']*100 for sub in evaluated_subs) / len(evaluated_subs)
                st.metric("Class Average Score", f"{avg_score:.1f}%")
                
                # Test-wise statistics
                st.subheader("Test-wise Performance")
                test_stats = {}
                for sub in evaluated_subs:
                    test_name = sub['test_name']
                    if test_name not in test_stats:
                        test_stats[test_name] = []
                    test_stats[test_name].append(sub['score']/sub['total_marks']*100)
                
                # Display test-wise averages
                col1, col2 = st.columns(2)
                for i, (test, scores) in enumerate(test_stats.items()):
                    avg = sum(scores) / len(scores)
                    with col1 if i % 2 == 0 else col2:
                        st.metric(f"{test} Average", f"{avg:.1f}%")
                
                # Show participation statistics
                st.subheader("Participation Statistics")
                st.metric("Total Submissions", len(evaluated_subs))
                st.metric("Number of Tests", len(test_stats))
            else:
                st.info("No evaluated submissions available")
        else:
            st.info("No data available for statistics")

if __name__ == "__main__":
    professor_dashboard()