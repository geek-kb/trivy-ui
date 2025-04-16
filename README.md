# Trivy UI

**Trivy UI** is a lightweight web-based dashboard and API service for exploring [Trivy](https://github.com/aquasecurity/trivy) vulnerability scan results. It allows you to upload JSON reports, view summaries, filter vulnerabilities, and drill down into individual findings.

---

## Project Structure

```
.
├── backend/         # FastAPI-based backend API
│   └── README.md    # Backend usage and development guide
├── frontend/        # React + Vite + Tailwind frontend
│   └── README.md    # Frontend usage and development guide
├── reports/         # Directory where reports are stored (created at runtime)
├── .gitignore
└── README.md        # This file
```

---

## Features

- Upload and parse Trivy JSON vulnerability reports
- View report metadata, summary, and full vulnerability listings
- Client-side sorting, pagination, and filtering
- Filter by severity, package name, CVE ID
- Interactive pie chart summary panel
- Responsive design with light/dark mode toggle
- RESTful API endpoints for automation

---

## Prerequisites

- [Trivy](https://github.com/aquasecurity/trivy) installed (for generating reports)
- Python 3.9+ for the backend
- Node.js 18+ for the frontend

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/trivy-ui.git
cd trivy-ui
```

### 2. Setup and Run the Backend

See detailed instructions in [backend/README.md](./backend/README.md)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Setup and Run the Frontend

See detailed instructions in [frontend/README.md](./frontend/README.md)

```bash
cd frontend
npm install
npm run dev
```

---

## Usage Example

Generate a Trivy JSON report:

```bash
trivy image --format json -o python_3_10-sbom.json python:3.10
```

Upload using curl:

```bash
curl -X POST http://localhost:8000/api/upload-report \
  -F "file=@python_3_10-sbom.json"
```

Or upload directly via the web UI at `http://localhost:5173`

---

## API Endpoints

The FastAPI backend is mounted at `/api`

- `POST /api/upload-report`: Upload a Trivy JSON file
- `GET /api/reports`: List all uploaded reports (with filters)
- `GET /api/report/{id}`: Get full report details
- `GET /api/report/{id}/summary`: Get high-level severity summary

---

## Deployment

You can deploy this project with Docker, Docker Compose, or on any platform that supports Node and Python. For production, make sure to use proper static file serving and HTTPS support.

---

## License

This project is open-sourced under the MIT License.

---

## Author & Acknowledgements

Built to simplify vulnerability triage using [Trivy](https://github.com/aquasecurity/trivy).

```

```
