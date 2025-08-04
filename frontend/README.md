# CV Parser Frontend

A simple frontend interface for parsing, filtering, and viewing resumes using a Flask + OCR backend.

Built with **React**, **TypeScript**, **Vite**, and **TailwindCSS**.

---

## 📁 Project Structure
```yaml
.
├── src
│ ├── api # API helper functions to interact with the backend
│ │ └── resume.ts
│ ├── components # Reusable UI components
│ │ ├── Dashboard.tsx # Main view showing all resumes
│ │ ├── FilterBar.tsx # Filter inputs to narrow down resumes
│ │ ├── ResumeCard.tsx # Individual resume display
│ │ └── UploadForm.tsx # File uploader for PDF resumes
│ ├── types # Type definitions
│ │ └── resume.d.ts
│ ├── App.tsx # Root component
│ ├── main.tsx # App entry point
│ ├── assets # Static assets (e.g., logos)
│ └── styles (.css) # Tailwind and custom styles
├── public # Public static files
├── vite.config.ts # Vite configuration
└── tsconfig*.json # TypeScript configuration
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/cv-parser-frontend.git
cd cv-parser-frontend
```
### 2. Install dependencies

```bash
npm install
```
### 3. Install dependencies
Create a .env file at the root of the project
```bash
VITE_API_BASE=http://127.0.0.1:5000
```
### 4. Run the development server
```bash
npm run dev
```
---
## Components Overview

### Dashboard.tsx
- Fetches and displays all resumes on load
- Renders a list of <ResumeCard />
- Includes:

  - <FilterBar /> for filtering resumes by name, city, degree, experience

  - <UploadForm /> for uploading new PDF files

### ResumeCard.tsx
Displays key resume information:
- Full name
- Email and phone
- Degrees, experience, and skills
- (Optional) CV link or ID
  
### FilterBar.tsx
- Interactive filters for:
- Name (keyword)
- City
- Degree type
- Minimum experience 
Calls filterResumes() from api/resume.ts and updates dashboard state.

### UploadForm.tsx
- Accepts a PDF file input
- Submits to the backend /upload route using FormData
- On success, triggers a resume refresh

---
## API Integration
All resume-related API calls are defined in "src/api/resume.ts"
## Types
Located in "src/types/resume.d.ts". Defines the Resume object structure returned by the backend.
---
## Tooling
- Vite – lightning-fast development server and bundler
- React + TypeScript – component-based frontend with strong typing
- Tailwind CSS – utility-first styling
- ESLint – code linting and formatting
- Prettier (optional) – consistent code formatting
