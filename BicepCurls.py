import sys
from PySide2 import QtCore, QtWidgets, QtGui
import cv2
import mediapipe as mp
import numpy as np

# Global variables
counter = 0
stage = None

# Function to calculate the angle
def calculate_angle(x, y, z):
    x = np.array(x)
    y = np.array(y)
    z = np.array(z)
    
    radians = np.arctan2(z[1] - y[1], z[0] - y[0]) - np.arctan2(x[1] - y[1], x[0] - y[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    return angle

# Custom QWidget for displaying video
class VideoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.video_frame = QtWidgets.QLabel()
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.video_frame)
        self.setLayout(layout)
    
    def set_frame(self, frame):
        # Convert frame to QImage
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        q_image = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        
        # Set QImage as QPixmap for QLabel
        pixmap = QtGui.QPixmap.fromImage(q_image)
        self.video_frame.setPixmap(pixmap)

# Custom QMainWindow for the application
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Dumbbell Curls Counter")
        
        # Create video widget
        self.video_widget = VideoWidget()
        self.setCentralWidget(self.video_widget)
        
        # Create counter label
        self.counter_label = QtWidgets.QLabel()
        self.counter_label.setAlignment(QtCore.Qt.AlignCenter)
        self.counter_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        # Create stage label
        self.stage_label = QtWidgets.QLabel()
        self.stage_label.setAlignment(QtCore.Qt.AlignCenter)
        self.stage_label.setStyleSheet("font-size: 18px;")
        
        # Create layout for counter and stage labels
        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(self.counter_label)
        label_layout.addWidget(self.stage_label)
        
        # Create main layout for the window
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(label_layout)
        main_layout.addWidget(self.video_widget)
        
        # Create central widget and set the main layout
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Initialize the video capture
        self.capture = cv2.VideoCapture(0)
        
        # Create a timer to periodically update the video frame
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)  # Update every 10 milliseconds
        
        # Initialize the stage and counter
        global stage, counter
        stage = None
        counter = 0
    
    def update_frame(self):
        ret, frame = self.capture.read()
        frame = cv2.flip(frame, 1)  # Flip the frame horizontally
        
        try:
            # Perform pose detection
            with mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb_frame)
                
                landmarks = results.pose_landmarks.landmark
                
                # Get coordinates of shoulder, elbow, and wrist
                shoulder = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value].y]
                
                # Calculate the angle
                angle = calculate_angle(shoulder, elbow, wrist)
                
                # Update counter and stage based on the angle
                if angle > 160:
                    stage = "Down"
                elif angle < 30 and stage == 'Down':
                    stage = "Up"
                    counter += 1
                    self.counter_label.setText(str(counter))
                
                # Display angle on the video frame
                cv2.putText(frame, str(angle), (int(elbow[0] * frame.shape[1]), int(elbow[1] * frame.shape[0])),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                
        except:
            pass
        
        # Render counter and stage labels
        self.stage_label.setText("Stage: " + stage)
        
        # Update video widget with the frame
        self.video_widget.set_frame(frame)
    
    def closeEvent(self, event):
        self.capture.release()
        event.accept()

# Main entry point
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
