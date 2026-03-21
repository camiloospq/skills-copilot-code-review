# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Read active school announcements from the database
- Manage announcements after signing in as a teacher or administrator

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get all activities with optional day and time filtering |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu&teacher_username=principal` | Sign up a student for an activity |
| POST | `/activities/{activity_name}/unregister?email=student@mergington.edu&teacher_username=principal` | Remove a student from an activity |
| POST | `/auth/login?username=principal&password=admin789` | Sign in a teacher or administrator |
| GET | `/auth/check-session?username=principal` | Validate a signed-in user |
| GET | `/announcements` | Get active announcements for the public site |
| GET | `/announcements/manage?teacher_username=principal` | Get all announcements for the management dialog |
| POST | `/announcements?teacher_username=principal` | Create an announcement with JSON body |
| PUT | `/announcements/{announcement_id}?teacher_username=principal` | Update an announcement with JSON body |
| DELETE | `/announcements/{announcement_id}?teacher_username=principal` | Delete an announcement |

## Data Model

The application stores data in MongoDB and seeds example records during startup when collections are empty.

1. Activities
   - Description
   - Structured schedule details
   - Maximum participant count
   - Registered student email addresses

2. Teachers
   - Username
   - Display name
   - Argon2 password hash
   - Role

3. Announcements
   - Title
   - Message
   - Optional start date
   - Required expiration date
   - Created and updated timestamps
