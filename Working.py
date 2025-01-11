import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

class WorkingStatus(Enum):
    WORKING = "Working"
    NOT_WORKING = "Not Working"

class ConcentrationLevel(Enum):
    DEEP = "Deep"
    MODERATE = "Moderate"
    LOW = "Low"

class ConcentrationDetector:
    def __init__(self, duration_minutes=None):
        # Initialize MediaPipe solutions
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Timing variables
        self.duration_minutes = duration_minutes
        self.start_time = None
        self.is_running = True

        # Status tracking
        self.current_status = WorkingStatus.NOT_WORKING
        self.status_history = deque(maxlen=90)  # 3 seconds at 30 FPS

        # Concentration metrics
        self.blink_history = deque(maxlen=180)  # 6 seconds
        self.face_position_history = deque(maxlen=90)  # 3 seconds
        self.expression_history = deque(maxlen=90)  # 3 seconds
        
        # Time tracking for concentration levels
        self.current_concentration_start = None
        self.time_in_current_concentration = 0

        # Duration tracking
        self.status_durations = {status: 0 for status in WorkingStatus}
        self.concentration_durations = {level: 0 for level in ConcentrationLevel}

        # Calibration values
        self.baseline_face_position = None
        self.calibration_frames = 60  # 2 seconds
        self.calibration_data = []

    def calibrate(self, frame):
        """Calibrate baseline face position for the user"""
        results = self.holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.face_landmarks:
            # Track nose position for face orientation
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

    def detect_working_status(self, results):
        """Detect if the user is working based on face detection"""
        if not results.face_landmarks:
            return WorkingStatus.NOT_WORKING

        # Check if user is facing the camera
        nose = results.face_landmarks.landmark[1]
        left_ear = results.face_landmarks.landmark[234]
        right_ear = results.face_landmarks.landmark[454]
        
        # Calculate head rotation
        ear_distance = abs(left_ear.x - right_ear.x)
        
        # If head is turned too much, consider not working
        if ear_distance < 0.08:  # Head turned too much
            return WorkingStatus.NOT_WORKING

        return WorkingStatus.WORKING

    def analyze_concentration(self, results, frame):
        """Analyze concentration level with more achievable thresholds"""
        if not results.face_landmarks:
            return ConcentrationLevel.LOW

        # Calculate scores
        face_position_score = self.analyze_face_position(results.face_landmarks)
        face_analysis_score = self.analyze_face(results.face_landmarks)
        stability_score = self.analyze_stability()

        # Calculate overall concentration score with adjusted weights
        concentration_score = (
            0.4 * face_position_score +
            0.4 * face_analysis_score +
            0.2 * stability_score
        )

        # More achievable thresholds
        if concentration_score > 0.675:  # Lowered threshold for deep concentration
            if self.current_concentration_start is None:
                self.current_concentration_start = datetime.now()
                self.time_in_current_concentration = 0
            else:
                self.time_in_current_concentration = (datetime.now() - self.current_concentration_start).seconds
            
            # Need 15 seconds (reduced from 30) of good concentration for deep concentration
            if self.time_in_current_concentration >= 15 and concentration_score > 0.65:
                return ConcentrationLevel.DEEP
            return ConcentrationLevel.MODERATE
        else:
            self.current_concentration_start = None
            self.time_in_current_concentration = 0
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

        # Calculate deviation from baseline position
        deviation = np.linalg.norm(current_nose_pos - self.baseline_face_position)
        position_score = max(0, 1 - (deviation * 3))  # More lenient scoring
        
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
        
        # Detect blink
        self.blink_history.append(avg_ear < 0.2)
        
        # Calculate blink rate (blinks per minute)
        blink_rate = sum(self.blink_history) * (60 / len(self.blink_history))
        
        # More lenient blink rate scoring (wider acceptable range)
        blink_score = max(0, 1 - abs(blink_rate - 17.5) / 25)
        
        # Analyze facial expression
        expression_score = self.analyze_expression(face_landmarks)
        
        return (blink_score * 0.4 + expression_score * 0.6)

    def analyze_expression(self, face_landmarks):
        """Analyze facial expression with more lenient scoring"""
        # Calculate eyebrow position
        left_eyebrow = face_landmarks.landmark[65].y
        right_eyebrow = face_landmarks.landmark[295].y
        
        # Calculate mouth tension
        mouth_left = face_landmarks.landmark[61]
        mouth_right = face_landmarks.landmark[291]
        mouth_width = abs(mouth_right.x - mouth_left.x)
        
        # More lenient scoring
        eyebrow_score = max(0, 1 - abs(0.35 - (left_eyebrow + right_eyebrow) / 2) * 2)
        mouth_score = max(0, 1 - abs(0.4 - mouth_width) * 1.5)
        
        expression_score = (eyebrow_score * 0.6 + mouth_score * 0.4)
        self.expression_history.append(expression_score)
        
        return np.mean(self.expression_history)

    def analyze_stability(self):
        """Analyze overall status stability"""
        if len(self.status_history) < 2:
            return 0.5
        
        # Calculate stability based on status changes
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

    def process_video_feed(self):
        """Process video feed and analyze concentration"""
        cap = cv2.VideoCapture(0)
        self.start_time = datetime.now()
        end_time = (self.start_time + timedelta(minutes=self.duration_minutes)) if self.duration_minutes else None

        print("Calibrating face position... Please look at the screen normally.")
        print(f"Calibration will take {self.calibration_frames/30:.1f} seconds...")
        
        calibrated = False
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                break

            # Process frame with MediaPipe
            results = self.holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            if not calibrated:
                calibrated = self.calibrate(frame)
                if calibrated:
                    print("Calibration complete! Starting concentration detection...")
                continue

            # Detect status and concentration
            status = self.detect_working_status(results)
            self.status_history.append(status)
            self.current_status = status
            
            concentration = self.analyze_concentration(results, frame)

            # Update durations
            self.status_durations[status] += 1/30  # Assuming 30 FPS
            self.concentration_durations[concentration] += 1/30

            # Display status
            self.display_status(frame, status, concentration)

            # Check time limit
            if end_time and datetime.now() >= end_time:
                break

            if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:
                break

        cap.release()
        cv2.destroyAllWindows()

    def display_status(self, frame, status, concentration):
        """Display current status on frame"""
        colors = {
            ConcentrationLevel.DEEP: (0, 255, 0),
            ConcentrationLevel.MODERATE: (0, 255, 255),
            ConcentrationLevel.LOW: (0, 0, 255)
        }

        # Display status and concentration
        cv2.putText(frame, f"Status: {status.value}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Concentration: {concentration.value}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors[concentration], 2)

        # Display concentration progress
        if self.current_concentration_start is not None:
            progress = min(self.time_in_current_concentration / 15 * 100, 100)
            cv2.putText(frame, f"Progress to Deep: {progress:.0f}%", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Display stats
        y_pos = 120
        for level in ConcentrationLevel:
            time = self.concentration_durations[level]
            cv2.putText(frame, f"{level.value}: {time:.1f}s", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors[level], 2)
            y_pos += 30

        cv2.imshow('Concentration Detector', frame)

    def get_report(self):
        """Generate detailed report of the session"""
        total_time = sum(self.concentration_durations.values())
        report = {
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
        return report

if __name__ == "__main__":
    duration = int(input("Enter session duration in minutes (0 for unlimited): "))
    duration = duration if duration > 0 else None
    
    detector = ConcentrationDetector(duration_minutes=duration)
    detector.process_video_feed()
    
    report = detector.get_report()
    print("\nSession Report:")
    print(f"Total Time: {report['total_time']:.2f} seconds")
    
    print("\nConcentration Breakdown:")
    for level, data in report['concentration_levels'].items():
        print(f"{level}: {data['time']:.2f}s ({data['percentage']:.1f}%)")
    
    print("\nWorking Status Breakdown:")
    for status, data in report['working_status'].items():
        print(f"{status}: {data['time']:.2f}s ({data['percentage']:.1f}%)")