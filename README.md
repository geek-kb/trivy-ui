# Trivy UI

A lightweight, secure, and modern web UI for browsing, filtering, and visualizing **Trivy vulnerability reports**.

---

## ✨ Features

- Upload **Trivy JSON**, **SPDX**, **CycloneDX**, or **.tar** vulnerability reports
- Drag-and-drop file uploads with file type and size validation (max 5MB)
- Client-side toast notifications for success and error feedback
- Pagination and dynamic page size selection
- Sort reports by Artifact, Timestamp, or Vulnerability severity (Critical, High, Medium, Low)
- Filter reports by Artifact name
- View report details with:
  - Severity breakdown via Pie Chart
  - Filters by Severity, Package Name, or CVE ID
  - Sorting vulnerabilities table
- All search, filters, sort state, and pagination are saved in the URL
- Backend validations:
  - Filename and Artifact name sanitization
  - Strict JSON schema validation (Pydantic)
  - File type & MIME type checks
  - IP extraction and future-proofing (rate limiting ready)
- Responsive design with **Dark Mode** support
- Optimized for developer and production deployments

---

## 🛠 Technologies Used

- **Frontend**

  - React + Vite
  - TypeScript
  - TailwindCSS
  - React Router
  - Recharts (for graphs)
  - React Hot Toast

- **Backend**

  - FastAPI
  - Pydantic (data validation)
  - Python 3.11+
  - Uvicorn

- **DevOps**
  - Docker & Docker Compose
  - Environment variable support for dev/prod

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/trivy-ui.git
cd trivy-ui
```

---

### 2. Set Up Environment Variables

Create two `.env` files:

- `.env.dev` for development
- `.env.prod` for production

Example `.env.dev`:

```env
BACKEND_PORT=8000
FRONTEND_PORT=5173
REPORTS_DIR=./reports
```

Example `.env.prod`:

```env
BACKEND_PORT=8000
FRONTEND_PORT=3000
REPORTS_DIR=./reports
```

✅ **Both files must exist before running Docker Compose.**

---

### 3. Running for Development

This mode runs the backend and frontend separately with hot reloading.

```bash
docker-compose --env-file .env.dev -f docker-compose.dev.yml up --build
```

- Frontend: <http://localhost:5173>
- Backend: <http://localhost:8000>

---

### 4. Running for Production

This mode builds static frontend assets and serves everything through the backend.

```bash
docker-compose --env-file .env.prod -f docker-compose.prod.yml up --build
```

- All traffic through: <http://localhost:8000>

---

## 🛣️ API Routes Documentation

| Method | Endpoint                      | Description                                            |
| :----- | :---------------------------- | :----------------------------------------------------- |
| GET    | `/`                           | Returns backend liveness message                       |
| GET    | `/health`                     | Health check endpoint (`{"status": "ok"}`)             |
| POST   | `/upload-report`              | Upload a vulnerability report file                     |
| POST   | `/report`                     | Upload a report by sending a JSON object (TrivyReport) |
| GET    | `/report/{report_id}`         | Fetch full report details and vulnerabilities          |
| GET    | `/report/{report_id}/summary` | Fetch only the report summary (counts)                 |
| GET    | `/reports`                    | List uploaded reports with optional filters            |

### `/reports` Query Parameters

- `artifact`: Search by artifact name (partial match)
- `min_critical`, `min_high`, `min_medium`, `min_low`: Minimum vulnerabilities of each severity
- `skip`: Pagination offset
- `limit`: Pagination size

Example:

```bash
curl "http://localhost:8000/reports?artifact=nginx&min_critical=1"
```

---

### `/report/{report_id}` Query Parameters

- `severity`: Filter vulnerabilities by severity (`CRITICAL`, `HIGH`, etc.)
- `pkgName`: Filter by package name (substring)
- `vulnId`: Filter by CVE/Vulnerability ID (substring)

Example:

```bash
curl "http://localhost:8000/report/1234-abcd?severity=HIGH&pkgName=openssl"
```

---

## 📂 Project Structure

```
backend/
  ├── app/
  │   ├── api/
  │   │   └── routes.py
  │   └── schemas/
  │       └── report.py
  └── Dockerfile

frontend/
  ├── src/
  │   ├── components/
  │   │   ├── UploadForm.tsx
  │   │   ├── ReportsList.tsx
  │   │   └── ReportDetail.tsx
  │   └── App.tsx
  └── Dockerfile

docker-compose.dev.yml
docker-compose.prod.yml
.env.dev
.env.prod
README.md
```

---

## 🧹 Best Practices Followed

- Secure file handling and strict input validation
- Separation of concerns between backend and frontend
- URL-driven search, filters, and pagination
- Detailed error reporting with meaningful messages
- Defensive backend programming (safe IDs, IP extraction, sanitization)
- Modern frontend with fast user interactions
- Ready for deployment in cloud environments

---

## 🩺 Health Check

```bash
curl http://localhost:8000/health
```

Expected output:

```json
{"status": "ok"}
```

---

## ✍️ Author

Created with ❤️ by **Itai Ganot**.

- GitHub: [https://github.com/geek-kb](https://github.com/geek-kb)
- LinkedIn: (optional to add if you want)

---

## 📜 License

MIT License — Free for personal and commercial use.
