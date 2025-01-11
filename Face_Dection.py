import cv2
import numpy as np
import mediapipe as mp
import time
from datetime import datetime

class ConcentrationDetector:
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize variables for concentration tracking
        self.start_time = None
        self.concentrated_time = 0
        self.concentration_threshold = 0.7
        self.looking_away_threshold = 30  # degrees
        
    def calculate_eye_aspect_ratio(self, eye_points):
        """Calculate the eye aspect ratio to detect blinks/closed eyes"""
        # Vertical eye landmarks
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        # Horizontal eye landmarks
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        # Eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def is_person_concentrated(self, frame):
        """Determine if the person is concentrated based on facial landmarks"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0].landmark
            
            # Get eye landmarks
            left_eye = np.array([[face_landmarks[p].x, face_landmarks[p].y] 
                               for p in [33, 160, 158, 133, 153, 144]])
            right_eye = np.array([[face_landmarks[p].x, face_landmarks[p].y] 
                                for p in [362, 385, 387, 263, 373, 380]])
            
            # Calculate eye aspect ratios
            left_ear = self.calculate_eye_aspect_ratio(left_eye)
            right_ear = self.calculate_eye_aspect_ratio(right_eye)
            
            # Get head pose estimation
            face_3d = []
            face_2d = []
            for idx, lm in enumerate(face_landmarks):
                if idx in [33, 263, 1, 61, 291, 199]:
                    x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
                    face_2d.append([x, y])
                    face_3d.append([x, y, lm.z])
            
            face_2d = np.array(face_2d, dtype=np.float64)
            face_3d = np.array(face_3d, dtype=np.float64)
            
            # Camera matrix
            focal_length = frame.shape[1]
            center = (frame.shape[1]/2, frame.shape[0]/2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)
            
            # Calculate head pose
            dist_matrix = np.zeros((4, 1), dtype=np.float64)
            success, rot_vec, trans_vec = cv2.solvePnP(
                face_3d, face_2d, camera_matrix, dist_matrix
            )
            
            # Get rotation angles
            rmat, jac = cv2.Rodrigues(rot_vec)
            angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
            
            # Check concentration criteria
            eyes_open = (left_ear + right_ear) / 2 > 0.2
            looking_forward = abs(angles[0]) < self.looking_away_threshold
            
            return eyes_open and looking_forward
        
        return False
    
    def process_video_feed(self):
        """Process live video feed and track concentration time"""
        cap = cv2.VideoCapture(0)
        self.start_time = datetime.now()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Check concentration
            is_concentrated = self.is_person_concentrated(frame)
            
            # Update concentrated time
            if is_concentrated:
                self.concentrated_time += 1/30  # Assuming 30 FPS
                
            # Display status
            status = "Concentrated" if is_concentrated else "Not Concentrated"
            cv2.putText(frame, f"Status: {status}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Concentrated Time: {self.concentrated_time:.2f}s",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display the frame
            cv2.imshow('Concentration Detector', frame)
            
            # Break loop on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        return self.concentrated_time

    def get_concentration_report(self):
        """Generate a report of concentration statistics"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        concentration_percentage = (self.concentrated_time / total_time) * 100 if total_time > 0 else 0
        
        return {
            'total_time': total_time,
            'concentrated_time': self.concentrated_time,
            'concentration_percentage': concentration_percentage
        }

# Example usage
if __name__ == "__main__":
    detector = ConcentrationDetector()
    print("Starting concentration detection... Press 'q' to quit")
    detector.process_video_feed()
    
    # Get and print report
    report = detector.get_concentration_report()
    print("\nConcentration Report:")
    print(f"Total Time: {report['total_time']:.2f} seconds")
    print(f"Concentrated Time: {report['concentrated_time']:.2f} seconds")
    print(f"Concentration Percentage: {report['concentration_percentage']:.2f}%")