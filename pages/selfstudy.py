import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import streamlit as st
import time
import logging
import os

# Suppress MediaPipe logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logging.getLogger('mediapipe').setLevel(logging.ERROR)

class WorkingStatus(Enum):
    WORKING = "Working"
    NOT_WORKING = "Not Working"

class ConcentrationLevel(Enum):
    DEEP = "Deep"
    MODERATE = "Moderate"
    LOW = "Low"

class ConcentrationDetector:
    def __init__(self, duration_minutes=None):
        # Initialize MediaPipe with optimized settings
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.3,  # Lowered for better performance
            min_tracking_confidence=0.3,
            model_complexity=0  # Use fastest model
        )
        
        # Initialize other attributes
        self.duration_minutes = duration_minutes
        self.start_time = None
        self.is_running = True
        self.frame_skip = 2  # Process every nth frame
        self.frame_count = 0
        self.initialize_tracking_variables()
        
    def initialize_tracking_variables(self):
        """Initialize all tracking variables with optimized settings"""
        self.current_status = WorkingStatus.NOT_WORKING
        self.status_history = deque(maxlen=30)  # Reduced history size
        self.blink_history = deque(maxlen=60)
        self.face_position_history = deque(maxlen=30)
        self.expression_history = deque(maxlen=30)
        self.current_concentration_start = None
        self.time_in_current_concentration = 0
        self.status_durations = {status: 0 for status in WorkingStatus}
        self.concentration_durations = {level: 0 for level in ConcentrationLevel}
        self.baseline_face_position = None
        self.calibration_frames = 30  # Reduced calibration frames
        self.calibration_data = []
        self.last_processed_result = None

    def calibrate(self, frame):
        """Calibrate baseline face position for the user"""
        frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        results = self.holistic.process(cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB))
        
        if results.face_landmarks:
            # Scale landmarks back to original frame size
            nose_pos = np.array([
                results.face_landmarks.landmark[1].x * 2,
                results.face_landmarks.landmark[1].y * 2,
                results.face_landmarks.landmark[1].z
            ])
            self.calibration_data.append(nose_pos)
            
            if len(self.calibration_data) == self.calibration_frames:
                self.baseline_face_position = np.mean(self.calibration_data, axis=0)
                return True
        return False

    def detect_working_status(self, results):
        """Optimized working status detection"""
        if not results.face_landmarks:
            return WorkingStatus.NOT_WORKING

        nose = results.face_landmarks.landmark[1]
        left_ear = results.face_landmarks.landmark[234]
        right_ear = results.face_landmarks.landmark[454]
        ear_distance = abs(left_ear.x - right_ear.x)
        
        # More lenient threshold for head rotation
        if ear_distance < 0.1:
            return WorkingStatus.NOT_WORKING

        return WorkingStatus.WORKING

    def analyze_concentration(self, results):
        """Optimized concentration analysis with adjusted thresholds"""
        if not results.face_landmarks:
            return ConcentrationLevel.LOW

        # Calculate weighted scores
        position_score = self.analyze_face_position(results.face_landmarks) * 0.35
        face_score = self.analyze_face(results.face_landmarks) * 0.35
        stability_score = self.analyze_stability() * 0.3

        total_score = position_score + face_score + stability_score

        # Adjusted thresholds
        if total_score > 0.6:
            if self.current_concentration_start is None:
                self.current_concentration_start = datetime.now()
            else:
                self.time_in_current_concentration = (datetime.now() - self.current_concentration_start).seconds
            
            if self.time_in_current_concentration >= 10 and total_score > 0.6:
                return ConcentrationLevel.DEEP
            return ConcentrationLevel.MODERATE
        else:
            self.current_concentration_start = None
            return ConcentrationLevel.LOW

    def analyze_face_position(self, face_landmarks):
        """Analyze face position relative to baseline"""
        if self.baseline_face_position is None:
            return 0.5

        current_nose_pos = np.array([
            face_landmarks.landmark[1].x,
            face_landmarks.landmark[1].y,
            face_landmarks.landmark[1].z
        ])

        deviation = np.linalg.norm(current_nose_pos - self.baseline_face_position)
        position_score = max(0, 1 - (deviation * 3))
        
        self.face_position_history.append(position_score)
        return np.mean(self.face_position_history)

    def analyze_face(self, face_landmarks):
        """Analyze facial features and eye state"""
        # Calculate eye aspect ratio
        left_eye = [face_landmarks.landmark[i] for i in [33, 160, 158, 133, 153, 144]]
        right_eye = [face_landmarks.landmark[i] for i in [362, 385, 387, 263, 373, 380]]
        
        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2
        
        self.blink_history.append(avg_ear < 0.2)
        blink_rate = sum(self.blink_history) * (60 / len(self.blink_history))
        blink_score = max(0, 1 - abs(blink_rate - 17.5) / 25)
        
        expression_score = self.analyze_expression(face_landmarks)
        
        return (blink_score * 0.4 + expression_score * 0.6)

    def analyze_expression(self, face_landmarks):
        """Analyze facial expression with optimized thresholds"""
        left_eyebrow = face_landmarks.landmark[65].y
        right_eyebrow = face_landmarks.landmark[295].y
        
        mouth_left = face_landmarks.landmark[61]
        mouth_right = face_landmarks.landmark[291]
        mouth_width = abs(mouth_right.x - mouth_left.x)
        
        eyebrow_score = max(0, 1 - abs(0.35 - (left_eyebrow + right_eyebrow) / 2) * 2)
        mouth_score = max(0, 1 - abs(0.4 - mouth_width) * 1.5)
        
        expression_score = (eyebrow_score * 0.6 + mouth_score * 0.4)
        self.expression_history.append(expression_score)
        
        return np.mean(self.expression_history)

    def analyze_stability(self):
        """Analyze overall status stability"""
        if len(self.status_history) < 2:
            return 0.5
        
        stability = 1.0 - (sum(a != b for a, b in zip(self.status_history, 
                                                     list(self.status_history)[1:])) / 
                          (len(self.status_history) - 1))
        return stability

    def calculate_ear(self, eye):
        """Calculate eye aspect ratio"""
        vertical_dist1 = np.linalg.norm(np.array([eye[1].x, eye[1].y]) - 
                                      np.array([eye[5].x, eye[5].y]))
        vertical_dist2 = np.linalg.norm(np.array([eye[2].x, eye[2].y]) - 
                                      np.array([eye[4].x, eye[4].y]))
        horizontal_dist = np.linalg.norm(np.array([eye[0].x, eye[0].y]) - 
                                       np.array([eye[3].x, eye[3].y]))
        return (vertical_dist1 + vertical_dist2) / (2 * horizontal_dist)

    def display_status(self, frame, status, concentration):
        """Display status on frame with optimized visuals"""
        colors = {
            ConcentrationLevel.DEEP: (0, 255, 0),
            ConcentrationLevel.MODERATE: (0, 255, 255),
            ConcentrationLevel.LOW: (0, 0, 255)
        }

        cv2.putText(frame, f"Status: {status.value}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Concentration: {concentration.value}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors[concentration], 2)

        if self.current_concentration_start is not None:
            progress = min(self.time_in_current_concentration / 10 * 100, 100)
            cv2.putText(frame, f"Progress to Deep: {progress:.0f}%", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        y_pos = 120
        for level in ConcentrationLevel:
            time = self.concentration_durations[level]
            cv2.putText(frame, f"{level.value}: {time:.1f}s", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors[level], 2)
            y_pos += 30

    def calibrate(self, frame):
        """Simple calibration method"""
        try:
            results = self.holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if results.face_landmarks:
                nose_pos = np.array([
                    results.face_landmarks.landmark[1].x,
                    results.face_landmarks.landmark[1].y,
                    results.face_landmarks.landmark[1].z
                ])
                self.calibration_data.append(nose_pos)
                if len(self.calibration_data) == self.calibration_frames:
                    self.baseline_face_position = np.mean(self.calibration_data, axis=0)
                    return True
            return False
        except Exception as e:
            st.error(f"Calibration error: {str(e)}")
            return False

    def process_frame(self, frame):
        """Optimized frame processing"""
        self.frame_count += 1
        
        # Skip frames for better performance
        if self.frame_count % self.frame_skip != 0:
            if self.last_processed_result:
                return self.last_processed_result
            return frame, WorkingStatus.NOT_WORKING, ConcentrationLevel.LOW

        # Resize frame for better performance
        frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        results = self.holistic.process(cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB))
        
        status = self.detect_working_status(results)
        concentration = self.analyze_concentration(results)
        
        self.status_durations[status] += self.frame_skip/30
        self.concentration_durations[concentration] += self.frame_skip/30
        
        # Scale landmarks back to original frame size
        if results.face_landmarks:
            for landmark in results.face_landmarks.landmark:
                landmark.x *= 2
                landmark.y *= 2
        
        self.display_status(frame, status, concentration)
        self.last_processed_result = (frame, status, concentration)
        return frame, status, concentration

    def get_report(self):
        """Generate session report"""
        total_time = sum(self.concentration_durations.values())
        return {
            'total_time': total_time,
            'concentration_levels': {
                level.value: {
                    'time': self.concentration_durations[level],
                    'percentage': (self.concentration_durations[level] / total_time * 100)
                    if total_time > 0 else 0
                } for level in ConcentrationLevel
            },
            'working_status': {
                status.value: {
                    'time': self.status_durations[status],
                    'percentage': (self.status_durations[status] / total_time * 100)
                    if total_time > 0 else 0
                } for status in WorkingStatus
            }
        }

    def process_video_feed(self):
        """Optimized video feed processing"""
        cap = None
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Reduced resolution
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not cap.isOpened():
                st.error("Failed to open camera feed")
                return None

            col1, col2 = st.columns([3, 1])
            
            with col1:
                frame_placeholder = st.empty()
                status_placeholder = st.empty()
                progress_placeholder = st.empty()
            
            with col2:
                session_timer = st.empty()
                stop_button = st.button("Stop Session")

            self.start_time = datetime.now()
            end_time = (self.start_time + timedelta(minutes=self.duration_minutes)) if self.duration_minutes else None

            # Optimized calibration
            with st.spinner("Calibrating..."):
                calibration_progress = st.progress(0)
                while len(self.calibration_data) < self.calibration_frames:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    self.calibrate(frame)
                    calibration_progress.progress(len(self.calibration_data) / self.calibration_frames)

            st.success("Calibration complete!")

            while not stop_button:
                ret, frame = cap.read()
                if not ret:
                    break

                processed_frame, status, concentration = self.process_frame(frame)
                rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                frame_placeholder.image(rgb_frame, use_container_width=True)
                status_placeholder.text(f"Status: {status.value} | Concentration: {concentration.value}")
                
                elapsed_time = datetime.now() - self.start_time
                if self.duration_minutes:
                    remaining_time = timedelta(minutes=self.duration_minutes) - elapsed_time
                    progress = min(elapsed_time.total_seconds() / (self.duration_minutes * 60), 1.0)
                    progress_placeholder.progress(progress)
                    session_timer.text(f"Remaining: {str(remaining_time).split('.')[0]}")
                else:
                    session_timer.text(f"Elapsed: {str(elapsed_time).split('.')[0]}")

                if end_time and datetime.now() >= end_time:
                    break

                time.sleep(0.01)

            return self.get_report()
            
        finally:
            if cap and cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()