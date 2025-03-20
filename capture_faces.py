import cv2
import os

def capture_faces():
    # Prompt user for details
    person_name = input("Enter the student's name: ").strip()
    roll_number = input("Enter the student's roll number: ").strip()
    department = input("Enter the student's department: ").strip()

    # Create dataset directory if it doesn't exist
    if not os.path.exists('dataset'):
        os.makedirs('dataset')

    # Create a folder for the person using their roll number as the unique identifier
    person_dir = os.path.join('dataset', roll_number)
    if not os.path.exists(person_dir):
        os.makedirs(person_dir)

    # Save metadata (name, roll number, department) in a text file inside the folder
    metadata_file = os.path.join(person_dir, 'metadata.txt')
    with open(metadata_file, 'w') as f:
        f.write(f"Name: {person_name}\n")
        f.write(f"Roll Number: {roll_number}\n")
        f.write(f"Department: {department}\n")

    # Initialize the camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend on Windows
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    print(f"Capturing images for {person_name} (Roll No: {roll_number}). Press 'q' to quit.")
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            # Draw a rectangle around the face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            # Save the captured face
            face_img = frame[y:y+h, x:x+w]
            img_path = os.path.join(person_dir, f"{roll_number}_{count}.jpg")
            cv2.imwrite(img_path, face_img)
            count += 1

            print(f"Captured {img_path}")

        # Display the frame
        cv2.imshow('Capture Faces', frame)

        # Break the loop if 'q' is pressed or if 50 images are captured
        if cv2.waitKey(1) & 0xFF == ord('q') or count >= 50:
            break

    # Release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_faces()