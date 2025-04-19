// frontend/src/App.tsx

import {useState, useEffect} from "react";
import {BrowserRouter as Router, Routes, Route, Link} from "react-router-dom";
import UploadForm from "./components/UploadForm";
import ReportsList from "./components/ReportsList";
import ReportDetail from "./components/ReportDetail";

export default function App() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== "undefined") {
      return (
        localStorage.getItem("theme") === "dark" ||
        (!localStorage.getItem("theme") &&
          window.matchMedia("(prefers-color-scheme: dark)").matches)
      );
    }
    return false;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 text-gray-800 dark:bg-gray-900 dark:text-white px-4 py-8 transition-colors">
        <div className="max-w-5xl mx-auto bg-white dark:bg-gray-800 p-6 sm:p-8 rounded-2xl shadow-md">
          {/* Header */}
          <header className="flex justify-between items-center mb-10">
            <Link to="/" className="flex items-center gap-3">
              <img
                src="/icon.png"
                alt="Trivy UI Logo"
                width={158}
                height={158}
                className="rounded"
              />
              <span className="text-4xl sm:text-6xl font-bold">Trivy UI</span>
            </Link>
            <button
              onClick={() => {
                setDarkMode((prev) => {
                  const newMode = !prev;
                  if (newMode) {
                    document.documentElement.classList.add("dark");
                  } else {
                    document.documentElement.classList.remove("dark");
                  }
                  return newMode;
                });
              }}
              className={`text-sm border px-3 py-1 rounded font-semibold transition-all duration-300 ease-in-out ${
                darkMode
                  ? "bg-white text-black hover:bg-gray-200" // If page is dark → button is white
                  : "bg-gray-800 text-white hover:bg-gray-700" // If page is light → button is dark
              }`}
            >
              {darkMode ? "☀️ Light Mode" : "🌙  Dark Mode"}
            </button>
          </header>

          {/* Subtitle */}
          <p className="text-center text-gray-600 dark:text-gray-300 mb-8">
            Explore security reports with filtering and summary views
          </p>

          {/* Routes */}
          <Routes>
            <Route
              path="/"
              element={
                <>
                  {/* Upload Form */}
                  <UploadForm />

                  {/* Reports List */}
                  <div className="mt-8">
                    <ReportsList />
                  </div>
                </>
              }
            />

            <Route
              path="/report/:id"
              element={<ReportDetail enableSeverityFilter={true} />}
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
