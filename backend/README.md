# Trivy UI Backend

This is the backend service for Trivy UI. It provides a RESTful API to manage and query Trivy vulnerability reports. Built with FastAPI and Pydantic, it enables uploading, storing, filtering, and retrieving detailed security reports in JSON format.

## Features

- Upload Trivy JSON reports (via API or file upload)
- Store reports on disk with metadata and UUID-based identification
- Filter vulnerabilities by severity, package name, and CVE ID
- Summarize severity levels per report
- Support for pagination and filtering across all stored reports
- Data model validation with Pydantic

## Endpoints

### `GET /`

Health check endpoint to confirm backend is running.

### `GET /health`

Returns `{ "status": "ok" }` to confirm service is healthy.

### `POST /report`

Upload a Trivy report via JSON body.

**Request body:**
`TrivyReport` (validated Pydantic model)

**Response:**

```json
{
  "id": "a76c38da-xxxx-xxxx-xxxx-2c1a9f36b37d",
  "artifact": "your-artifact-name"
}
```

### `POST /upload-report`

Upload a Trivy report as a file (JSON format only).

**Request:**
`multipart/form-data` with `.json` file

**Response:**
Same as `/report` endpoint.

### `GET /report/{report_id}`

Get detailed report data with filtering.

**Query parameters:**

- `severity`: one or more severity values (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`)
- `pkgName`: substring filter for package names
- `vulnId`: substring filter for CVE ID

**Response:**
Includes report summary and filtered vulnerabilities.

### `GET /report/{report_id}/summary`

Returns a severity-level breakdown of a specific report.

### `GET /reports`

List all stored reports with optional filtering and pagination.

**Query parameters:**

- `skip`: offset for pagination (default: 0)
- `limit`: number of results (default: 20)
- `artifact`: filter by artifact name
- `min_critical`, `min_high`, `min_medium`, `min_low`: minimum thresholds per severity

**Response:**
Paginated report summaries with severity counts.

## Requirements

- Python 3.9+
- Trivy reports in JSON format

## Setup

```bash
pip install -r requirements.txt
```

Run the application:

```bash
uvicorn app.main:app --reload
```

By default, reports are saved to the `reports/` directory relative to the backend root.

## Directory Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI router and logic
│   ├── schemas/report.py     # Pydantic model for Trivy reports
├── reports/                  # Saved report files
├── requirements.txt
```

## Notes

- Only `.json` files are accepted.
- Uploaded reports are automatically assigned an `id` and timestamped.
- Artifact names can be customized or fallback to the filename.

## License

This project is licensed under the MIT License.
