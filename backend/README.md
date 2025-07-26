# CV Parser Backend
This is the backend of the CV Parser project, designed to extract structured data from unstructured PDF resumes using NLP, layout analysis, regex, OCR, and fuzzy matching. Built with **Python (Flask)** and connected to a **MySQL** database, it provides a RESTful API for uploading, parsing, storing, filtering, and retrieving resume data.

## Architecture Overview

backend/
│
├── app.py                        # Flask app entry point
├── routes/                       # All API route logic
│   └── router.py
│
├── models/                       # DB schema & database interaction
│   └── resume.py
│
├── parser/                       # Core extraction logic
│   ├── cv_parser.py             # Orchestrates full parsing flow
│   ├── layout_analyser.py       # PDF reader + layout/OCR engine
│   ├── name_city_extraction.py
│   ├── email_phone_extraction.py
│   ├── skills_experience_extraction.py
│   ├── status_occupation_extraction.py
│   ├── degree_extraction.py
│   ├── utils/
│   │   ├── helper.py            # Text utils, config, cities/skills/etc.
│   │   └── constants/           # Data files (JSON, lists)
│   ├── pdfs/                   # Real PDFs for testing
│   └── test-modules/            # Dev testing of isolated modules
│
├── temp/                         # Temporary folder for uploaded PDFs
└── .env                          # Environment variables (DB credentials, etc.)

## Features
- Upload and parse PDFs with layout + OCR fallback.
- NLP with spaCy for named entity recognition.
- Fuzzy search for cities and keyword-based filtering.
- Degree and education extraction via regex and config patterns.
- Modular extraction logic for maintainability and testing.
- MySQL relational DB with foreign keys (resumes, skills, degrees).
- REST API for integration with frontends or other systems.

## Setup Instructions
1. Clone repository
```bash
git clone https://github.com/BigB021/cvParser.git
cd cv-parser/backend
```
or:
```bash
gh repo clone BigB021/cvParser
cd cv-parser/backend
```
2. Create a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate

```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4. Install OCR dependencies
```bash
sudo apt install tesseract-ocr
```
5. Install spaCy pre-trained language models (English and French)
```bash
python -m spacy download en_core_web_md 
python -m spacy download fr_core_news_md
```
Lighter models:
```bash
python -m spacy download en_core_web_sm
python -m spacy download fr_core_news_sm
```
6. Set up MySQL and .env
```bash
user=mysql_username
password=mysql_password
```
7. Run the app
```bash
python app.py
```
## API Routes
| Method | Endpoint                 | Description                       |
| ------ | ------------------------ | --------------------------------- |
| GET    | `/`                      | Basic test route                  |
| GET    | `/resumes/`              | Get all resumes                   |
| GET    | `/resumes/<id>`          | Get resume by ID                  |
| GET    | `/resumes/email/<email>` | Get resume by email               |
| GET    | `/resumes/search?name=X` | Search resume by name             |
| GET    | `/resumes/filter?params` | Filter by city, degree, exp, etc. |
| POST   | `/resumes/`              | Add resume JSON manually          |
| DELETE | `/resumes/<id>`          | Delete resume                     |
| POST   | `/resumes/upload`        | Upload a PDF resume and parse it  |

## Parsing Logic
All parsing is orchestrated in:

parser/cv_parser.py → process_and_store_resume(path)

Extraction logic is modularized into:

- extract_name() → Name (via layout and NER)
- extract_city() → Moroccan city (via fuzzy match)
- extract_email() and extract_phone_number() → Regex
- extract_degrees() → Degree subject/type from text
- extract_skills() → Based on known headers/keywords
- extract_experience_years() → Based on config sections
- extract_status() → e.g. Student, Intern, Employed
- extract_occupation() → Role from text/NLP

## Database Schema
- resumes

id, name, email, phone, city, occupation, exp_years, status, pdf_path

- degrees

 resume_id, degree_type, degree_subject

- skills

resume_id, skill_name

All relations are maintained using FOREIGN KEY ON DELETE CASCADE.

## Technologies
| Tool/Lib        | Use case                     |
| --------------- | ---------------------------- |
| Flask           | REST API framework           |
| PyMuPDF         | PDF parsing/layout           |
| pytesseract     | OCR fallback                 |
| spaCy           | NER for name/occupation      |
| mysql-connector | DB connection                |
| dotenv          | Environment config           |
| rapidfuzz       | Fuzzy matching (e.g. cities) |

## Dev Tips
- To test a module in isolation, run its __main__ block
- Logs are printed with [Debug] or [Warning]
- To analyze new PDFs: place them in parser/pdfs/ and run cv_parser.py