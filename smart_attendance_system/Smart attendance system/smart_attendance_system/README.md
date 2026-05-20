# Smart Attendance System

Production-oriented Flask project for automating classroom attendance from a single classroom image using RetinaFace and ArcFace.

## Features

This version includes:

- Complete project folder structure
- Python dependency list
- Flask application initialization
- SQLite database setup with schema
- Base dashboard template and static assets
- Student registration form and student list
- Multiple face image upload per student
- ArcFace embedding generation through InsightFace pretrained models
- SQLite storage for student details, image paths, and embedding paths
- Attendance generation from a classroom image
- Manual correction checklist before saving final attendance
- Reports dashboard with date and student filters
- JSON APIs for students and attendance reports
- Manual NumPy implementations for grayscale conversion, convolution filtering, and Sobel edge detection

## Setup

```bash
cd smart_attendance_system
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app init-db
flask --app app run
```

Open `http://127.0.0.1:5000`.

## Recommended Run Steps

On Ubuntu/Debian, install the Python virtual environment package first if it is
not already installed:

```bash
sudo apt update
sudo apt install -y python3.10-venv python3-pip build-essential cmake libgl1 libglib2.0-0
```

1. Create and activate a virtual environment.

```bash
cd "/media/vinay/Multimedia/Project related/Smart attendance system/smart_attendance_system"
python3 -m venv .venv
source .venv/bin/activate
```

2. Upgrade packaging tools.

```bash
python3 -m pip install --upgrade pip setuptools wheel
```

3. Install dependencies.

```bash
python3 -m pip install -r requirements.txt
```

4. Create the environment file.

```bash
cp -n .env.example .env
```

5. Initialize the SQLite database.

```bash
python3 -m flask --app app init-db
```

6. Start the Flask server.

```bash
python3 -m flask --app app run --host 127.0.0.1 --port 5000
```

7. Open the app.

```text
http://127.0.0.1:5000
```

## Workflow

1. Go to `Students > Register`.
2. Add student details and upload multiple clear face images.
3. Go to `Attendance`.
4. Upload one classroom image.
5. Review the AI-generated checklist.
6. Correct checkboxes if needed.
7. Save final attendance.
8. Open `Reports` to filter records by date or student.

## Folder Structure

```text
smart_attendance_system/
├── app.py
├── config.py
├── requirements.txt
├── database/
│   ├── db.py
│   └── schema.sql
├── models/
├── routes/
├── services/
├── utils/
├── static/
│   ├── css/
│   └── js/
├── templates/
├── uploads/
├── embeddings/
└── README.md
```

## Database

The schema stores students, uploaded student face images, ArcFace embedding files,
attendance sessions, and final attendance records.

SQLite is used first. The code keeps database access inside the `database/` package
so repository classes can later be swapped for MongoDB without changing route or
service logic.

## Student Registration Module

Routes:

- `GET /students/` lists registered students.
- `GET /students/register` shows the registration form.
- `POST /students/register` saves student details, uploads images, generates embeddings, and stores records in SQLite.

Uploaded student images are saved under `uploads/students/<student_id>/`.
Generated ArcFace embeddings are saved as `.npy` files under `embeddings/students/<student_id>/`.

The first embedding request can take longer because InsightFace loads pretrained
model files. If the model files are not cached locally, InsightFace may download
them into its model cache.

## Face Recognition Pipeline

Pipeline service:

- [services/recognition_pipeline.py](services/recognition_pipeline.py)

Processing flow:

1. `RetinaFaceDetectionService` detects all faces in the classroom image.
2. `ArcFaceRecognitionService` crops each detected face and generates a normalized ArcFace embedding.
3. `FaceMatchingService` compares the face embedding with stored student embeddings using cosine similarity.
4. Faces with similarity below `COSINE_MATCH_THRESHOLD` are returned as `unknown`.

Recognition thresholds are configured separately in:

- [recognition_config.py](recognition_config.py)
- `.env`

Relevant environment variables:

```bash
COSINE_MATCH_THRESHOLD=0.45
RETINAFACE_CONFIDENCE_THRESHOLD=0.90
MINIMUM_FACE_SIZE=32
ARCFACE_MODEL_NAME=buffalo_l
ARCFACE_PROVIDERS=CPUExecutionProvider
```

Example service usage:

```python
from pathlib import Path

from services.recognition_pipeline import FaceRecognitionPipeline

results = FaceRecognitionPipeline().recognize_classroom_image(
    Path("uploads/classroom/sample.jpg")
)

for result in results:
    print(result.status, result.full_name, result.similarity, result.bounding_box)
```

## Attendance Generation Module

Routes:

- `GET /attendance/capture` shows the classroom image upload page.
- `POST /attendance/capture` runs RetinaFace + ArcFace recognition and creates an editable attendance draft.
- `POST /attendance/save` saves teacher-corrected attendance records.
- `GET /attendance/sessions/<session_id>` shows the saved attendance for one session.

Present/absent logic:

- All registered students start as absent.
- Students recognized by the face pipeline above `COSINE_MATCH_THRESHOLD` are marked present.
- Duplicate recognitions for the same student keep the highest cosine similarity.
- The teacher can correct every student with a checkbox before saving.
- Saved records include status, similarity confidence, and whether the teacher manually corrected the AI prediction.

## Reports

Routes:

- `GET /reports/` shows the reports dashboard.
- Filter by `date=YYYY-MM-DD`.
- Filter by `student_id=<id>`.

JSON APIs:

- `GET /api/students`
- `GET /api/attendance`
- `GET /api/attendance?date=YYYY-MM-DD`
- `GET /api/attendance?student_id=1`

## Manual Image Processing Utilities

Implemented in [utils/image_processing.py](utils/image_processing.py):

- `to_grayscale(image, channel_order="rgb")`
- `convolve2d(image, kernel)`
- `sobel_edges(image, channel_order="rgb")`

These functions use NumPy directly and are kept separate from the deep learning
pipeline so they can be demonstrated, tested, or reused for preprocessing
experiments without changing RetinaFace or ArcFace behavior.

## Notes

- The first InsightFace or RetinaFace run may take time while pretrained model files are prepared or downloaded.
- Use clear registration images with one student face per image.
- Classroom photos should have visible, front-facing student faces for best results.
- SQLite is used initially; repository classes isolate database access for a future MongoDB migration.

## Dependency Troubleshooting

If student registration fails with an error like:

```text
AttributeError: module 'ml_dtypes' has no attribute 'float4_e2m1fn'
```

Reinstall the pinned ONNX and ml-dtypes versions inside the virtual environment:

```bash
source .venv/bin/activate
python3 -m pip install --force-reinstall "onnx==1.16.2" "ml-dtypes==0.4.1"
```

Then restart Flask.

If attendance capture fails with:

```text
ValueError: You have tensorflow 2.17.0 and this requires tf-keras package.
```

Install the matching TensorFlow Keras compatibility package:

```bash
source .venv/bin/activate
python3 -m pip install "tf-keras==2.17.0"
```

Then restart Flask.
