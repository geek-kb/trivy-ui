# Trivy UI

A modern, secure, and lightweight web UI for browsing, filtering, and visualizing **Trivy vulnerability reports**.

---

## ✨ Features

- Upload Trivy `.json`, `.spdx.json`, `.cdx.json`, or `.tar` vulnerability reports
- Drag-and-drop file uploads with file type, size, and JSON content validation
- Real-time toast notifications for upload and validation feedback
- Sorting by Artifact Name, Timestamp, and all Severity levels
- Pagination with rows-per-page selection and page state in URL
- Full text search by Artifact name
- View report details with:
  - Severity breakdown Pie Chart
  - Vulnerability filters by Severity, Package Name, and CVE ID
  - CVE links to external CVE records
- Optimized for Developer and Production environments
- Dark Mode support out-of-the-box
- Strict backend validations (JSON schema, size limits, safe filenames)

---

## 🛠 Technologies Used

**Frontend**

- React + Vite
- TypeScript
- TailwindCSS
- React Router
- Recharts (Pie charts)
- React Hot Toast (Notifications)

**Backend**

- FastAPI (Python 3.11+)
- Pydantic (Strict schema validation)
- Uvicorn (ASGI server)

**DevOps**

- Docker & Docker Compose
- Environment variables support (`.env.dev`, `.env.prod`)

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/trivy-ui.git
cd trivy-ui
```

---

### 2. Set up Environment Variables

Create two environment files:

- `.env.dev` (for development)
- `.env.prod` (for production)

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

✅ Both `.env` files must exist before running Docker Compose.

---

### 3. Run in Development Mode

Separate backend and frontend containers with hot-reloading.

```bash
docker-compose --env-file .env.dev -f docker-compose.dev.yml up --build
```

Access:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>

---

### 4. Run in Production Mode

Single backend container serving both API and frontend static files.

```bash
docker-compose --env-file .env.prod -f docker-compose.prod.yml up --build
```

Access:

- All traffic: <http://localhost:8000>

---

## 📂 Project Structure

```
backend/
  ├── app/
  │   ├── api/routes.py
  │   └── schemas/report.py
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

## 🛣️ API Routes

| Method | Endpoint                      | Description                                   |
| :----- | :---------------------------- | :-------------------------------------------- |
| GET    | `/`                           | Backend liveness check                        |
| GET    | `/health`                     | Health check endpoint                         |
| POST   | `/upload-report`              | Upload a file (validated Trivy JSON)          |
| POST   | `/report`                     | Upload a report directly as JSON body         |
| GET    | `/report/{report_id}`         | Fetch full report details and vulnerabilities |
| GET    | `/report/{report_id}/summary` | Fetch report summary only                     |
| GET    | `/reports`                    | List all uploaded reports with filters        |

### `/reports` Query Parameters

- `artifact`: Filter by artifact name
- `min_critical`, `min_high`, `min_medium`, `min_low`: Minimum vulnerabilities by severity
- `skip` and `limit`: Pagination

### `/report/{report_id}` Query Parameters

- `severity`: Filter vulnerabilities by severity
- `pkgName`: Filter vulnerabilities by package name
- `vulnId`: Filter vulnerabilities by vulnerability ID

---

## 🧹 Best Practices

- Strong server-side validation
- Filename and Artifact name sanitization
- Upload size limits
- MIME type and extension validation
- IP handling and rate limiting support ready
- Frontend and Backend clean separation

---

## 🩺 Health Check

Simple backend health endpoint:

```bash
curl http://localhost:8000/health
```

Expected output:

```json
{"status": "ok"}
```

---

## 📋 TODOs (Planned Improvements)

| Item                             | Description                                                                                    |
| :------------------------------- | :--------------------------------------------------------------------------------------------- |
| Kubernetes Support               | Create Kubernetes manifests for backend, frontend, and a shared volume for reports             |
| Helm Chart                       | Package the project as a Helm chart for easier Kubernetes deployment                           |
| Database Integration             | Add support for using PostgreSQL / SQLite (based on env variable switch) instead of filesystem |
| API Authentication               | Add API token-based or JWT authentication (optional read-only/public mode)                     |
| Rate Limiting                    | Protect the upload endpoints from abuse                                                        |
| RBAC (Role Based Access Control) | Create admin and viewer roles for more secure access                                           |
| TLS                              | Support HTTPS inside the backend container                                                     |
| External Storage                 | Add option to save reports to AWS S3 / GCS / Azure Blob                                        |
| Multi-User Support               | (optional) Associate reports to different users if auth is added                               |
| Export Reports                   | Add ability to download filtered reports from UI                                               |
| WebSocket / Live Updates         | Push updates if new reports are uploaded                                                       |

---

## ✍️ Author

Created with ❤️ by **Itai Ganot**.

- GitHub: [https://github.com/geek-kb](https://github.com/geek-kb)

---

## 📜 License

MIT License — Free for personal and commercial use.
