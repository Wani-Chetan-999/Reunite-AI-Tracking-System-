# Reunite AI Tracking System

An AI-powered missing person tracking and reunification platform built to help identify, track, and reconnect missing individuals using computer vision, location tracking, and intelligent case management.

---

## Overview

The Reunite AI Tracking System is designed to assist authorities and organizations in managing missing person cases efficiently. The platform leverages AI-based image recognition, location management, and centralized case handling to improve the chances of locating and reuniting missing individuals.

The system provides:

* Missing person case registration
* AI-assisted tracking support
* Police station management
* Real-time location handling
* Face recognition and surveillance integration
* Secure admin and user management
* Data storage and tracking dashboards

---

## Features

### Core Features

* Missing person registration system
* Upload and manage case details
* Police station management module
* Location-based tracking
* Face recognition integration
* AI-assisted identification
* RTSP camera support
* Case status monitoring
* Dashboard for administrators
* Secure authentication system

### AI & Tracking Features

* Face detection and recognition
* Image comparison support
* Surveillance camera integration
* Location data processing
* Automated tracking workflows

---

## Tech Stack

### Backend

* Python
* Django
* Celery
* Redis

### Frontend

* HTML
* CSS
* JavaScript

### Database

* SQLite / Django ORM

### AI & Computer Vision

* OpenCV
* AI-based facial recognition

---

## Project Structure

```bash
Reunite-AI-Tracking-System-
│
├── Reunite/                 # Main Django project
├── cases/                   # Missing person case management
├── police/                  # Police station module
├── templates/               # HTML templates
├── static/                  # CSS, JS, Images
├── manage.py                # Django management file
├── rtspCam.py               # RTSP camera integration
├── requirements.txt         # Project dependencies
├── locations.csv            # Location dataset
├── police_stations.csv      # Police station dataset
└── README.md
```

---

## Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/Wani-Chetan-999/Reunite-AI-Tracking-System-.git
cd Reunite-AI-Tracking-System-
```

---

### 2. Create Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Run Database Migrations

```bash
python manage.py migrate
```

---

### 5. Start Redis Server

#### Linux

```bash
sudo service redis-server start
```

#### Check Redis Version

```bash
redis-cli --version
redis-server --version
```

---

### 6. Start Celery Worker

```bash
celery -A Reunite worker -l info -P solo
```

---

### 7. Run Development Server

```bash
python manage.py runserver
```

Open in browser:

```bash
http://127.0.0.1:8000/
```

---

## RTSP Camera Integration

The system supports RTSP camera streaming for surveillance and real-time monitoring.

Run:

```bash
python rtspCam.py
```

---

## Dependencies

Important libraries used:

* Django
* OpenCV
* Celery
* Redis
* NumPy
* Pillow

Install all dependencies using:

```bash
pip install -r requirements.txt
```

---

## Use Cases

* Missing person tracking
* Disaster recovery operations
* Child safety monitoring
* Public surveillance systems
* Smart city safety projects
* Police investigation support

---

## Future Enhancements

* Real-time GPS tracking
* Mobile application integration
* Cloud deployment
* Live AI alerts
* Multi-language support
* Advanced analytics dashboard
* Automated notification system

---

## Screenshots


```bash
/assets/screenshots/
```

Example:

* Dashboard
* Case Registration
* AI Detection Results
* Tracking Map
* Camera Feed

---

## Security Features

* Authentication system
* Secure case management
* Controlled access for admins
* Data validation
* Session management

---

## License

This project is licensed under the MIT License.

---

## Author

### Chetan Wani

* Information Technology Student
* AI & Full Stack Developer
* Interested in Computer Vision, AI Systems, and Smart Safety Solutions

GitHub:

[Wani-Chetan-999 GitHub Profile](https://github.com/Wani-Chetan-999?utm_source=chatgpt.com)

---

## Contributing

Contributions are welcome.

Steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

---

## Repository

[Reunite AI Tracking System Repository](https://github.com/Wani-Chetan-999/Reunite-AI-Tracking-System-?utm_source=chatgpt.com)
