# Ps & Qs Meeting Queue Manager

A full-stack office hours and meeting queue management system designed for professors, TAs, and students.

Ps & Qs helps manage office hours queues with real-time queue tracking, student authentication, priority queue handling, dashboard tools, and email notification support.

---

# Features

## Student Features
- Create student accounts using valid CWIDs
- Secure login authentication
- View available office hours sessions
- Join office hours queues
- View real-time queue position
- Cancel active queue requests
- Persistent profile management
- DSS / priority queue support
- Queue position restoration after refresh

## Professor / TA Features
- Professor account creation
- Dashboard access control
- View active queue
- View next student
- Serve next student
- Create office hours sessions
- View queue statistics

## Queue System Features
- Two-tier priority queue system
    - DSS students
    - Non-DSS students
- First-Come, First-Serve (FCFS) within each tier
- Persistent queue storage using SQLite
- Session-based queue support
- Queue restoration after backend restart
- Queue cancellation tracking
- Queue notes support
- Queue reset per session

## Notification Features
- Email queue confirmation
- Near-front queue notifications
- Background email worker
- Persistent email jobs
- Retry handling for failed email sends

---

# Tech Stack

## Frontend
- React
- Vite
- TailwindCSS

## Backend
- Python
- Flask
- Flask-CORS

## Database
- SQLite

## Deployment
- Render

---

# Project Architecture

```text
Frontend (React/Vite)
        ↓
Flask REST API
        ↓
Queue Engine + SQLite Database
        ↓
Background Email Worker
```

---

# Queue System Design

The queue engine uses a two-tier priority system:

```text
Tier 1: DSS students
Tier 2: Non-DSS students
```

Within each tier:
- First-Come, First-Serve ordering is maintained.

The system also:
- Prevents duplicate active queue requests
- Tracks queue positions
- Persists queue data between restarts
- Supports queue session separation

---

# Account System

## Student Accounts
Students create accounts using:
- Valid CWID
- School email
- Password

CWIDs are pre-seeded into the database for demo purposes.

## Professor Accounts
Professor accounts use internally generated IDs and include:
- Dashboard access
- Queue management permissions

---

# Email Notification System

The notification service supports:
- Background email processing
- Retry behavior
- Scheduled notifications
- Queue confirmation emails
- Near-front notifications

Email jobs are stored persistently in the database.

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/rtledev/Project-Queue-Manager.git
cd Project-Queue-Manager
```

---

# Backend Setup

## 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate environment:

### Windows
```bash
.venv\Scripts\activate
```

### Linux / Mac
```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com
```

---

## 5. Run Backend

```bash
python app.py
```

Backend runs on:

```text
http://127.0.0.1:5000
```

---

# Frontend Setup

## 6. Navigate to Frontend

```bash
cd Front-End
```

---

## 7. Install Frontend Dependencies

```bash
npm install
```

---

## 8. Run Frontend

```bash
npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

# Deployment

## Backend Deployment (Render)

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
gunicorn app:app
```

---

# Frontend Deployment

Frontend can be deployed using:
- Render Static Site
- GitHub Pages
- Netlify
- Vercel

---

# Environment Variables

## Frontend `.env`

```env
VITE_API_BASE_URL=https://your-backend-url.onrender.com
```

---

# API Endpoints

## Authentication
- `POST /api/auth/signup`
- `POST /api/auth/login`

## Queue
- `POST /api/join-queue`
- `POST /api/cancel-queue`
- `GET /api/queue/<student_id>/position`

## Dashboard
- `POST /api/dashboard/queue`
- `POST /api/dashboard/next-student`
- `POST /api/dashboard/serve-next`
- `POST /api/dashboard/queue-counts`

## Office Hours
- `GET /api/office-hours`

---

# Current Project Status

## Completed
- Queue engine implementation
- Persistent SQLite storage
- Authentication system
- Dashboard system
- Queue management
- Email notification system
- React frontend integration
- Session queue support

## In Progress
- Multiple simultaneous queues
- Calendar integration
- UI improvements
- Enhanced permissions system
- Improved email templates
- Real-time updates

---

# Future Improvements
- WebSocket live queue updates
- PostgreSQL migration
- Docker deployment
- Role-based permissions
- Queue analytics
- Mobile responsiveness improvements
- Scheduled office hours
- Real-time notifications

---

# Contributors

## Team 8 - SoBS

- Richard Le
- Israel Zavala

---

# Screenshots

---

# License

This project is for educational and academic purposes.

---

# Acknowledgements

Built as part of:
- CPSC 362 - Software Engineering
- California State University, Fullerton