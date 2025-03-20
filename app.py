from flask import Flask, render_template, Response, jsonify, request
import cv2
import face_recognition
import pickle
import pandas as pd
import os
import datetime

app = Flask(__name__)

# Load the trained model
with open('trained_model/model.pkl', 'rb') as f:
    model_data = pickle.load(f)
known_face_encodings = model_data["encodings"]
known_face_names = model_data["names"]

# Attendance CSV file
attendance_file = "attendance.csv"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_attendance')
def get_attendance():
    # Load attendance data
    if not os.path.exists(attendance_file):
        return jsonify([])  # Return an empty list if the file doesn't exist

    try:
        df = pd.read_csv(attendance_file)
        attendance_data = df.to_dict(orient='records')  # Convert DataFrame to a list of dictionaries
        return jsonify(attendance_data)
    except pd.errors.EmptyDataError:
        return jsonify([])  # Return an empty list if the file is empty

@app.route('/modify_records', methods=['POST'])
def modify_records():
    data = request.get_json()
    name = data.get('name')
    action = data.get('action')

    if not os.path.exists(attendance_file):
        return jsonify({"message": "Attendance file does not exist."}), 400

    try:
        df = pd.read_csv(attendance_file)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=["Name", "Roll Number", "Department", "Timestamp"])

    if action == "add":
        # Extract metadata from the name (e.g., "John Doe (12345, CS)")
        parts = name.split("(")
        student_name = parts[0].strip()
        roll_number, department = parts[1].strip(")").split(", ")
        department = department.strip()

        new_entry = pd.DataFrame({
            "Name": [student_name],
            "Roll Number": [roll_number],
            "Department": [department],
            "Timestamp": [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(attendance_file, index=False)
        return jsonify({"message": f"Added {name} to records."})

    elif action == "delete":
        # Extract metadata from the name (e.g., "John Doe (12345, CS)")
        parts = name.split("(")
        student_name = parts[0].strip()
        roll_number, department = parts[1].strip(")").split(", ")
        department = department.strip()

        if ((df['Name'] == student_name) & (df['Roll Number'] == roll_number)).any():
            df = df[~((df['Name'] == student_name) & (df['Roll Number'] == roll_number))]
            df.to_csv(attendance_file, index=False)
            return jsonify({"message": f"Deleted {name} from records."})
        else:
            return jsonify({"message": f"{name} not found in records."}), 404

    elif action == "modify":
        # Placeholder for modification logic
        return jsonify({"message": f"Modification for {name} is not implemented yet."}), 501

    else:
        return jsonify({"message": "Invalid action."}), 400

@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Save the uploaded file temporarily
        upload_path = os.path.join("uploads", file.filename)
        file.save(upload_path)

        # Process the uploaded image
        try:
            image = face_recognition.load_image_file(upload_path)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            marked_attendance = []
            for face_encoding in face_encodings:
                # Compare with known faces
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                if True in matches:
                    match_index = matches.index(True)
                    name = known_face_names[match_index]

                # Mark attendance
                if name != "Unknown":
                    mark_attendance(name)
                    marked_attendance.append(name)

            # Delete the temporary file
            os.remove(upload_path)

            return jsonify({
                "message": "Attendance marked successfully",
                "marked_attendance": marked_attendance
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template('upload.html')

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend on Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Set frame width to 640px
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set frame height to 480px
    cap.set(cv2.CAP_PROP_FPS, 30)            # Set FPS to 30

    frame_skip = 2  # Process every 2nd frame to reduce computation
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:  # Skip frames
            continue

        # Resize the frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        # Convert the frame to RGB
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all face locations and encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")  # Use HOG instead of CNN
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale back up face locations since the frame was resized
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            # Compare the face with known faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = known_face_names[match_index]

                # Mark attendance (with error handling)
                try:
                    mark_attendance(name)
                except Exception as e:
                    print(f"Error marking attendance: {e}")

            # Draw a rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def mark_attendance(name):
    # Attendance CSV file
    attendance_file = "attendance.csv"

    # Check if the file exists
    if not os.path.exists(attendance_file):
        # Create the file with headers if it doesn't exist
        with open(attendance_file, 'w') as f:
            f.write("Name,Roll Number,Department,Timestamp\n")

    # Load existing attendance data
    try:
        df = pd.read_csv(attendance_file)
    except pd.errors.EmptyDataError:
        # If the file is empty, create an empty DataFrame with the correct columns
        df = pd.DataFrame(columns=["Name", "Roll Number", "Department", "Timestamp"])

    try:
        # Validate and parse the name
        if "(" not in name or ")" not in name:
            print(f"Invalid name format: {name}. Skipping attendance marking.")
            return

        # Split the name into parts
        parts = name.split("(")
        if len(parts) < 2:
            print(f"Invalid name format: {name}. Skipping attendance marking.")
            return

        student_name = parts[0].strip()
        metadata = parts[1].strip(")").split(", ")

        if len(metadata) < 2:
            print(f"Invalid metadata format: {name}. Skipping attendance marking.")
            return

        roll_number = metadata[0].strip()
        department = metadata[1].strip()

        # Validate extracted metadata
        if not student_name or not roll_number.isdigit() or not department:
            print(f"Invalid metadata for {name}. Skipping attendance marking.")
            return

        # Generate a unique key for the person
        unique_key = f"{student_name}_{roll_number}"

        # Check if the person already exists in the DataFrame
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if unique_key in df['Name'] + "_" + df['Roll Number'].astype(str):
            # Update the timestamp for the existing record
            mask = (df['Name'] == student_name) & (df['Roll Number'] == roll_number)
            df.loc[mask, 'Timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"Updated timestamp for {name}")
        else:
            # Add a new entry
            new_entry = pd.DataFrame({
                "Name": [student_name],
                "Roll Number": [roll_number],
                "Department": [department],
                "Timestamp": [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
            df = pd.concat([df, new_entry], ignore_index=True)
            print(f"Attendance marked for {name}")

        # Explicitly remove duplicates based on Name and Roll Number
        df = df.drop_duplicates(subset=["Name", "Roll Number"], keep="last")

        # Save the updated DataFrame back to the CSV file
        df.to_csv(attendance_file, index=False)

        # Print the final state of the DataFrame for debugging
        print("Final DataFrame after update:")
        print(df)

    except Exception as e:
        print(f"Error processing attendance for {name}: {e}")

import os

if __name__ == '__main__':
    # Ensure the uploads directory exists
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    # Use the environment variable PORT for deployment
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    