import streamlit as st
import json
from datetime import datetime
from pages.selfstudy import ConcentrationDetector, ConcentrationLevel
import threading
import time

class TestMonitor:
    def __init__(self, test_duration):
        self.concentration_detector = ConcentrationDetector(duration_minutes=test_duration)
        self.concentration_history = []
        self.monitoring_thread = None
        self.is_monitoring = False
        self._stop_event = threading.Event()
        
    def start_monitoring(self):
        """Start concentration monitoring in a separate thread"""
        self.is_monitoring = True
        self._stop_event.clear()
        self.monitoring_thread = threading.Thread(target=self._monitor_concentration)
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """Safely stop the monitoring thread and cleanup resources"""
        if self.is_monitoring:
            self._stop_event.set()
            self.is_monitoring = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
            self.concentration_detector.holistic.close()  # Close MediaPipe resources
        
    def _monitor_concentration(self):
        """Background thread for monitoring concentration"""
        try:
            report = self.concentration_detector.process_video_feed()
            if report:
                self.concentration_history = report
        finally:
            self.is_monitoring = False
            
    def get_concentration_warning(self):
        """Calculate if a warning is needed based on concentration levels"""
        if not self.concentration_history:
            return None
            
        total_time = self.concentration_history['total_time']
        if total_time == 0:
            return None
            
        low_concentration_time = self.concentration_history['concentration_levels']['Low']['time']
        low_concentration_percentage = (low_concentration_time / total_time) * 100
        
        if low_concentration_percentage > 70:
            return {
                'warning': True,
                'message': f"Low concentration detected for {low_concentration_percentage:.1f}% of the test duration.",
                'details': self.concentration_history
            }
        return None

def load_test(test_id):
    try:
        with open('tests.json', 'r') as f:
            tests = json.load(f)
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

def cleanup_monitoring():
    """Helper function to clean up monitoring resources"""
    if 'test_monitor' in st.session_state and st.session_state.test_monitor:
        st.session_state.test_monitor.stop_monitoring()
        del st.session_state.test_monitor

def test_interface():
    st.title("Test Interface")
    
    # Initialize test monitor in session state if not present
    if 'test_monitor' not in st.session_state:
        st.session_state.test_monitor = None
    
    if 'current_test' not in st.session_state:
        # Show available tests
        try:
            with open('tests.json', 'r') as f:
                tests = json.load(f)
                if not tests:
                    st.warning("No tests available")
                    return
                    
                test_options = [f"{test['name']} - {test['subject']}" for test in tests]
                selected_index = st.selectbox("Select Test", range(len(test_options)), 
                                           format_func=lambda x: test_options[x])
                
                if st.button("Start Test"):
                    st.session_state.current_test = tests[selected_index]['id']
                    # Initialize concentration monitoring
                    test_duration = tests[selected_index]['duration']
                    st.session_state.test_monitor = TestMonitor(test_duration)
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
            cleanup_monitoring()
            return
            
        st.header(f"{test['name']} - {test['subject']}")
        st.write(f"Duration: {test['duration']} minutes")
        st.write(f"Total Marks: {test['total_marks']}")
        
        # Start concentration monitoring if not already started
        if st.session_state.test_monitor and not st.session_state.test_monitor.is_monitoring:
            st.session_state.test_monitor.start_monitoring()
        
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
            # Get concentration warning if any
            warning = None
            if st.session_state.test_monitor:
                warning = st.session_state.test_monitor.get_concentration_warning()
                cleanup_monitoring()  # Stop monitoring and cleanup resources
            
            submission = {
                'student': st.session_state.username,
                'test_id': st.session_state.current_test,
                'test_name': test['name'],
                'answers': st.session_state.answers,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'id': f"sub_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'concentration_warning': warning if warning else None
            }
            
            save_submission(submission)
            
            if warning:
                st.warning(warning['message'])
                st.info("This warning has been recorded with your submission.")
            
            st.success("Test submitted successfully!")
            
            # Clear test state
            del st.session_state.current_test
            del st.session_state.answers
        
        # Return to dashboard
        if col2.button("Return to Dashboard"):
            cleanup_monitoring()  # Stop monitoring and cleanup resources
            st.switch_page("pages/student_dashboard.py")

if __name__ == "__main__":
    test_interface()