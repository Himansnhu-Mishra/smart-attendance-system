import os
import face_recognition
import pickle

def train_model():
    # Create trained_model directory if it doesn't exist
    if not os.path.exists('trained_model'):
        os.makedirs('trained_model')

    # Load all images from the dataset folder
    known_face_encodings = []
    known_face_names = []
    known_metadata = []  # To store metadata (name, roll number, department)

    for roll_number in os.listdir('dataset'):
        person_dir = os.path.join('dataset', roll_number)
        if os.path.isdir(person_dir):
            # Load metadata
            metadata_file = os.path.join(person_dir, 'metadata.txt')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = f.readlines()
                    name = metadata[0].split(":")[1].strip()
                    roll_number = metadata[1].split(":")[1].strip()
                    department = metadata[2].split(":")[1].strip()
                    display_name = f"{name} ({roll_number}, {department})"
            else:
                display_name = roll_number  # Fallback if metadata is missing

            print(f"Training on images of {display_name}...")

            for image_name in os.listdir(person_dir):
                if image_name.endswith('.jpg'):  # Only process image files
                    image_path = os.path.join(person_dir, image_name)
                    image = face_recognition.load_image_file(image_path)
                    face_encoding = face_recognition.face_encodings(image)

                    if len(face_encoding) > 0:
                        known_face_encodings.append(face_encoding[0])
                        known_face_names.append(display_name)
                        known_metadata.append({
                            "name": name,
                            "roll_number": roll_number,
                            "department": department
                        })
                    else:
                        print(f"No face detected in {image_name}")

    # Save the trained model and metadata
    model_data = {
        "encodings": known_face_encodings,
        "names": known_face_names,
        "metadata": known_metadata  # Include metadata in the model
    }
    with open('trained_model/model.pkl', 'wb') as f:
        pickle.dump(model_data, f)

    print("Model training completed and saved.")

if __name__ == "__main__":
    train_model()