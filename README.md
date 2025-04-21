# Trivy UI

A modern, secure, and lightweight web UI for browsing, filtering, and visualizing **Trivy vulnerability reports**.

---

## ✨ Features

- Upload Trivy `.json`, `.spdx.json`, `.cdx.json`, or `.tar` vulnerability reports
- Drag-and-drop file uploads with file type, size, and JSON structure validation
- Real-time toast notifications for success/failure feedback
- Sorting by Artifact Name, Timestamp, Critical, High, Medium, and Low vulnerabilities
- Pagination with rows-per-page selection and page state stored in URL
- Full text search by Artifact name
- View report details:
  - Severity breakdown Pie Chart
  - Filter vulnerabilities by Severity, Package Name, CVE ID
  - Direct links to CVE databases
- Optimized for both Development and Production environments
- Dark Mode ready (TailwindCSS)
- Strict backend validation (schema, file size, safe filenames)
- Timestamps automatically adjusted to your configured timezone
- Lightweight footprint (~100MB images)
- Internal API metrics (`/api/metrics` — total number of reports)

---

## 🛠 Technologies Used

**Frontend**

- React (Vite)
- TypeScript
- TailwindCSS
- React Router
- Recharts (Charts library)
- React Hot Toast (Notifications)

**Backend**

- FastAPI (Python 3.11+)
- Uvicorn (ASGI server)
- Pydantic + pydantic-settings
- SQLAlchemy Core (Optional for DB backends)
- dotenv (.env support)
- Async/Await optimized

**DevOps**

- Docker & Docker Compose
- Clean separation of frontend/backend
- Environment overrides for Dev/Prod
- Health checks and metrics endpoints

---

## UI screenshots

![Trivy UI - Main Page - Reports List](./trivy-ui-reports-list.png)
![Trivy UI - Main Page - Report Details](./trivy-ui-report-details.png)

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/trivy-ui.git
cd trivy-ui
```

---

### 2. Set up Environment Variables

Backend `.env` (inside `backend/.env`):

```env
# Backend environment
ENV=development
TIMEZONE=Asia/Jerusalem
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# Storage backend options: filesystem / sqlite / postgres
DB_BACKEND=filesystem
FILESYSTEM_STORAGE_DIR=backend/app/storage/reports
# POSTGRES_URL=postgresql+asyncpg://user:password@localhost:5432/trivyui
# SQLITE_PATH=backend/trivy_ui.db
```

---

### 3. Build and Run Locally

```bash
docker-compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)

---

## 📂 Project Structure

```bash
.
├── ./CONTRIBUTING.md
├── ./LICENSE
├── ./README.md
├── ./backend
│   ├── ./backend/Dockerfile
│   ├── ./backend/README.md
│   ├── ./backend/app
│   │   ├── ./backend/app/api
│   │   │   └── ./backend/app/api/routes.py
│   │   ├── ./backend/app/core
│   │   │   ├── ./backend/app/core/config.py
│   │   │   ├── ./backend/app/core/database.py
│   │   │   └── ./backend/app/core/exception_handlers.py
│   │   ├── ./backend/app/main.py
│   │   ├── ./backend/app/models
│   │   │   └── ./backend/app/models/report.py
│   │   ├── ./backend/app/schemas
│   │   │   └── ./backend/app/schemas/report.py
│   │   └── ./backend/app/storage
│   │   ├── ./backend/app/storage/base.py
│   │   ├── ./backend/app/storage/factory.py
│   │   ├── ./backend/app/storage/filesystem.py
│   │   ├── ./backend/app/storage/postgres.py
│   │   ├── ./backend/app/storage/reports
│   │   └── ./backend/app/storage/sqlite.py
│   ├── ./backend/logging.yaml
│   ├── ./backend/logs
│   │   └── ./backend/logs/README.md
│   ├── ./backend/requirements.txt
├── ./docker-compose.override.yml
├── ./docker-compose.prod.yml
├── ./docker-compose.yml
├── ./frontend
│   ├── ./frontend/Dockerfile
│   ├── ./frontend/Dockerfile.dev
│   ├── ./frontend/README.md
│   ├── ./frontend/dist
│   │   ├── ./frontend/dist/assets
│   │   │   ├── ./frontend/dist/assets/index-CpjW13Wg.css
│   │   │   └── ./frontend/dist/assets/index-Gatrr9HR.js
│   │   └── ./frontend/dist/index.html
│   ├── ./frontend/eslint.config.js
│   ├── ./frontend/index.html
│   ├── ./frontend/nginx
│   │   ├── ./frontend/nginx/default.conf
│   │   └── ./frontend/nginx/nginx.conf
│   ├── ./frontend/postcss.config.js
│   ├── ./frontend/public
│   ├── ./frontend/src
│   │   ├── ./frontend/src/App.css
│   │   ├── ./frontend/src/App.tsx
│   │   ├── ./frontend/src/api.ts
│   │   ├── ./frontend/src/components
│   │   │   ├── ./frontend/src/components/Chart.css
│   │   │   ├── ./frontend/src/components/LoadingSpinner.tsx
│   │   │   ├── ./frontend/src/components/ReportDetail.tsx
│   │   │   ├── ./frontend/src/components/ReportsList.tsx
│   │   │   └── ./frontend/src/components/UploadForm.tsx
│   │   ├── ./frontend/src/index.css
│   │   ├── ./frontend/src/main.tsx
│   │   └── ./frontend/src/vite-env.d.ts
│   ├── ./frontend/tailwind.config.js
│   └── ./frontend/vite.config.ts
├── ./k8s
│   ├── ./k8s/backend
│   │   ├── ./k8s/backend/backend-deployment.yaml
│   │   ├── ./k8s/backend/backend-pv.yaml
│   │   ├── ./k8s/backend/backend-pvc.yaml
│   │   └── ./k8s/backend/backend-service.yaml
│   └── ./k8s/frontend
│   ├── ./k8s/frontend/frontend-deployment.yaml
│   ├── ./k8s/frontend/frontend-ingress.yaml
│   └── ./k8s/frontend/frontend-service.yaml
├── ./trivy-ui-report-details.png
└── ./trivy-ui-reports-list.png
```

---

## 🧪 API Endpoints

| Method | Endpoint             | Description                                |
| :----- | :------------------- | :----------------------------------------- |
| GET    | `/api/`              | Root alive check                           |
| GET    | `/api/health`        | Health check endpoint                      |
| GET    | `/api/metrics`       | Returns number of stored reports           |
| POST   | `/api/upload-report` | Upload Trivy file                          |
| POST   | `/api/report`        | Upload Trivy JSON via body                 |
| GET    | `/api/report/{id}`   | Fetch specific report details              |
| GET    | `/api/reports`       | List reports (with filters and pagination) |

---

## ⚙️ Configuration Options

| Variable                 | Description                                      | Example                       |
| :----------------------- | :----------------------------------------------- | :---------------------------- |
| `TIMEZONE`               | Timezone name for timestamps (pytz format)       | `Asia/Jerusalem`              |
| `DB_BACKEND`             | `filesystem`, `sqlite`, or `postgres` backend    | `filesystem`                  |
| `FILESYSTEM_STORAGE_DIR` | Path for storing uploaded reports locally        | `backend/app/storage/reports` |
| `POSTGRES_URL`           | PostgreSQL connection string (if using postgres) | `postgresql+asyncpg://...`    |
| `SQLITE_PATH`            | SQLite database path (if using sqlite)           | `backend/trivy_ui.db`         |

---

## 📈 Health & Metrics

Check health:

```bash
curl http://localhost:8000/api/health
```

Expected:

```json
{"status": "ok"}
```

Check metrics (total reports count):

```bash
curl http://localhost:8000/api/metrics
```

Expected:

```json
{"reports_count": 42}
```

---

## 🧹 Best Practices Implemented

- **Strict file upload validation:** max 5MB, `.json` or `.tar` only
- **Safe filenames** via sanitization
- **Automatic timezone correction** for reports
- **Rate limiting** support (IP-based, internal)
- **Frontend error boundaries**
- **Docker healthchecks ready**
- **Clear CORS policies** for dev vs prod
- **Strict typing across codebase (TypeScript and Python)**

---

## 📋 TODOs and Future Improvements

| Item                         | Description                                                  |
| :--------------------------- | :----------------------------------------------------------- |
| Kubernetes Support           | Helm chart + manifests for EKS, GKE, AKS                     |
| API Authentication           | Bearer tokens, API keys or JWTs                              |
| Rate Limiting Enforcement    | per IP rate limiter to prevent abuse                         |
| RBAC Roles                   | Admin vs Viewer accounts                                     |
| HTTPS in Docker              | Enable TLS termination in backend                            |
| Multi-user Mode              | Associate reports to different users if authentication added |
| External Storage Support     | Upload directly to AWS S3, GCS, or Azure Blob                |
| Live Updates                 | Implement WebSocket for real-time UI refresh                 |
| Export Filtered Reports      | Allow users to download filtered reports as JSON             |
| Trivy Integration (Optional) | Trigger Trivy scans directly via UI (with credentials)       |

---

## ✍️ Author

Created with ❤️ by **Itai Ganot**

- GitHub: [geek-kb](https://github.com/geek-kb)

---

## 📜 License

MIT License — free to use, modify, distribute, and build on.
