#  CV Parser

A full-stack application for parsing, extracting, and managing resume data from PDF files.  
The system uses **OCR**, **NLP**, **layout analysis**, and **regex** to transform unstructured resumes into structured entries stored in a **MySQL** database.

---

##  Tech Stack

| Layer     | Tech                                                                 |
|-----------|----------------------------------------------------------------------|
| Frontend  | React, TypeScript, Vite, TailwindCSS                                 |
| Backend   | Python, Flask, spaCy, PyMuPDF, Tesseract OCR, MySQL                  |
| Utilities | RapidFuzz, python-dotenv, mysql-connector, dateutil                  |

---

##  Features

- Upload and parse PDF resumes with OCR fallback
- Extract name, contact, skills, degrees, experience, and more
- Filter resumes by name, city, degree, and experience
- Clean UI to browse parsed resumes
- Modular architecture for testing and expansion

---

##  Project Structure
```yaml
cvParser/
├── backend/
│ ├── app.py # Flask entry point
│ ├── parser/ # CV parsing modules (layout, skills, degrees, etc.)
│ ├── routes/ # API routes
│ ├── models/ # DB schema and logic
│ ├── temp/ # Uploaded PDF storage
│ ├── .env # Environment config (MySQL, etc.)
│ └── requirements.txt
└── frontend/
├── src/
│ ├── components/ # UI components (Dashboard, ResumeCard, etc.)
│ ├── api/ # API request handlers
│ ├── types/ # TypeScript type definitions
├── .env # VITE_API_BASE
└── vite.config.ts
```
---

##  Getting Started

### Backend Setup

Check backend readme file [Here](https://github.com/BigB021/cvParser/blob/main/backend/README.md)

### Frontend setup 
Check frontend readme file [Here](https://github.com/BigB021/cvParser/blob/main/frontend/README.md)

