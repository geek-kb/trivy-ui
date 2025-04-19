# Contributing to Trivy UI

First off, thank you for considering contributing to **Trivy UI**!
Your help is what makes this project great. ❤️

This document provides a simple guide on how to contribute effectively.

---

## 📋 How to Contribute

1. **Fork** the repository.
2. **Clone** your forked repo locally:

   ```bash
   git clone https://github.com/your-username/trivy-ui.git
   cd trivy-ui
   ```

3. **Create a new branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make your changes** (see below for guidelines).
5. **Commit** your changes:

   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push** your branch to GitHub:

   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a **Pull Request** from your branch to the `main` branch of this repo.

---

## 🚀 Development Setup

You can run everything locally with Docker:

```bash
docker-compose up --build
```

- Frontend at: <http://localhost:3000>
- Backend API at: <http://localhost:8000>

Make sure you have `.env` files inside the `backend/` folder for local setup.

---

## 🛠 Code Style Guidelines

### Frontend (React + TypeScript)

- Use **TypeScript** for everything (no `.js` files).
- Prefer **functional components** and **hooks**.
- Keep components **small and focused**.
- Format your code with **Prettier** and **ESLint** (auto-run before commits preferred).

### Backend (FastAPI + Python 3.11+)

- Follow **PEP8** style guide.
- Type hint every function and class properly.
- Use **async/await** for all database and I/O operations.
- Catch and handle exceptions properly (don't leak stack traces to users).

---

## 🧪 Testing Guidelines

- Test all new features manually.
- If backend features touch data manipulation, add at least basic integration tests.
- Make sure backend API stays backward compatible if possible.

---

## 📂 Suggested Branch Naming

| Branch Type | Prefix Example              |
| :---------- | :-------------------------- |
| Feature     | `feature/add-upload-limit`  |
| Bugfix      | `fix/missing-health-check`  |
| Chore       | `chore/update-docs`         |
| Refactor    | `refactor/improve-database` |

---

## 🔥 What You Can Help With

- UI improvements (better sorting, grouping)
- Add more report filtering options (date range, package names)
- Backend performance optimizations
- Adding authentication support
- Improving deployment options (Helm chart, K8s manifests)
- Write better error handling and validation
- Write docs and tutorials
- Translating the UI (i18n)

---

## 📜 License

By contributing to this repository, you agree that your contributions will be licensed under the **MIT License**.

---

Thanks for making Trivy UI better! 🚀
