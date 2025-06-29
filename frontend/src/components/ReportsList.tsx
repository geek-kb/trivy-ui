// File: frontend/src/components/ReportsList.tsx

import {useEffect, useState, useCallback} from "react";
import {useSearchParams} from "react-router-dom";
import LoadingSpinner from "./LoadingSpinner";

interface ReportSummary {
  id: string;
  artifact: string;
  timestamp: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export default function ReportsList() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [artifactInput, setArtifactInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchParams, setSearchParams] = useSearchParams();
  const sortField =
    (searchParams.get("sortField") as keyof ReportSummary) || "timestamp";
  const sortDir = (searchParams.get("sortDir") as "asc" | "desc") || "desc";
  const page = Number(searchParams.get("page")) || 1;
  const pageSize = Number(searchParams.get("pageSize")) || 10;

  const countSeverities = (report: any, level: string): number => {
    return (
      report?.Results?.flatMap((r: any) => r.Vulnerabilities || []).filter(
        (v: any) => v.Severity?.toUpperCase() === level,
      ).length || 0
    );
  };

  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/reports`);
      if (!res.ok) throw new Error(await res.text());
      const raw = await res.json();

      console.log("Raw backend data:", raw);

      const normalized = Array.isArray(raw)
        ? raw.map((r) => ({
            id: r.UID || r.ID || r.id || "unknown-id",
            artifact: r.ArtifactName || r.artifact || "unknown",
            timestamp: r.CreatedAt || r.timestamp || "",
            critical: countSeverities(r, "CRITICAL"),
            high: countSeverities(r, "HIGH"),
            medium: countSeverities(r, "MEDIUM"),
            low: countSeverities(r, "LOW"),
          }))
        : [];

      console.log("Normalized reports:", normalized);
      setReports(normalized);
      setSelected(new Set());
    } catch (e: any) {
      console.error("Fetch reports error:", e);
      setError(e.message || "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
    const handler = () => fetchReports();
    window.addEventListener("reports:refresh", handler);
    return () => window.removeEventListener("reports:refresh", handler);
  }, [fetchReports]);

  const handleSort = (field: keyof ReportSummary) => {
    const dir = field === sortField && sortDir === "asc" ? "desc" : "asc";
    searchParams.set("sortField", field);
    searchParams.set("sortDir", dir);
    searchParams.set("page", "1");
    setSearchParams(searchParams);
  };

  const filtered = reports.filter((r) =>
    r.artifact?.toLowerCase?.().includes(artifactInput.toLowerCase()),
  );
  const sorted = [...filtered].sort((a, b) => {
    const A = a[sortField];
    const B = b[sortField];
    if (typeof A === "number" && typeof B === "number") {
      return sortDir === "asc" ? A - B : B - A;
    }
    return sortDir === "asc"
      ? String(A).localeCompare(String(B))
      : String(B).localeCompare(String(A));
  });
  const paginated = sorted.slice((page - 1) * pageSize, page * pageSize);
  const totalPages = Math.max(Math.ceil(sorted.length / pageSize), 1);

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };
  const toggleAll = () => {
    const allIds = paginated.map((r) => r.id);
    const hasAll = allIds.every((id) => selected.has(id));
    setSelected(hasAll ? new Set() : new Set(allIds));
  };

  const deleteSelected = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} reports?`)) return;
    try {
      const res = await fetch("/api/reports", {
        method: "DELETE",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({report_ids: Array.from(selected)}),
      });
      if (!res.ok) throw new Error((await res.text()) || "Unknown error");
      await fetchReports();
      setSelected(new Set());
    } catch (e: any) {
      console.error("Delete error:", e);
      alert(`Failed to delete selected reports: ${e.message}`);
    }
  };

  const badge = (n: number, sev: string) => {
    const base =
      sev === "critical"
        ? "bg-red-600 text-white"
        : sev === "high"
          ? "bg-orange-500 text-white"
          : sev === "medium"
            ? "bg-yellow-400 text-black"
            : "bg-blue-400 text-white";
    return (
      <span
        className={`inline-block min-w-[32px] px-1.5 py-0.5 rounded text-xs font-bold ${base}`}
      >
        {n}
      </span>
    );
  };

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="mt-20 text-center text-red-500">
        <p>{error}</p>
        <button
          onClick={fetchReports}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
        >
          Retry
        </button>
      </div>
    );

  return (
    <section className="mt-10 space-y-6">
      <div className="flex flex-col md:flex-row gap-4">
        <input
          type="text"
          placeholder="Search by artifact"
          value={artifactInput}
          onChange={(e) => {
            setArtifactInput(e.target.value);
            searchParams.set("page", "1");
            setSearchParams(searchParams);
          }}
          className="border px-3 py-2 rounded flex-1 text-black bg-white dark:text-white dark:bg-gray-800"
        />
      </div>

      {reports.length > 0 && (
        <button
          onClick={deleteSelected}
          disabled={selected.size === 0}
          className="px-4 py-2 bg-red-600 text-white dark:text-white rounded disabled:opacity-50"
        >
          Delete Selected ({selected.size})
        </button>
      )}

      {reports.length === 0 ? (
        <p className="text-center text-gray-400">No reports found.</p>
      ) : (
        <div className="overflow-auto rounded-lg shadow ring-1 ring-black ring-opacity-5">
          <table className="min-w-full divide-y divide-gray-700 text-sm">
            <thead className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white">
              <tr>
                <th className="px-4 py-2 text-center font-bold">
                  <input
                    type="checkbox"
                    checked={
                      paginated.length > 0 &&
                      paginated.every((r) => selected.has(r.id))
                    }
                    onChange={toggleAll}
                  />
                </th>
                {[
                  {label: "Artifact", field: "artifact"},
                  {label: "Timestamp", field: "timestamp"},
                  {label: "Critical", field: "critical"},
                  {label: "High", field: "high"},
                  {label: "Medium", field: "medium"},
                  {label: "Low", field: "low"},
                ].map((col) => (
                  <th
                    key={col.field}
                    onClick={() => handleSort(col.field as keyof ReportSummary)}
                    className={`px-4 py-2 cursor-pointer font-bold ${
                      ["artifact", "timestamp"].includes(col.field)
                        ? "text-left"
                        : "text-center"
                    }`}
                  >
                    {col.label}{" "}
                    {sortField === col.field && (sortDir === "asc" ? "↑" : "↓")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginated.map((r) => (
                <tr
                  key={r.id}
                  className="hover:bg-gray-200 dark:hover:bg-gray-700"
                >
                  <td className="px-4 py-2 text-center">
                    <input
                      type="checkbox"
                      checked={selected.has(r.id)}
                      onChange={() => toggleSelect(r.id)}
                    />
                  </td>
                  <td className="px-4 py-2">
                    <a
                      href={`/api/report/${r.id}`}
                      className="text-blue-600 dark:text-blue-300 hover:underline"
                    >
                      {r.artifact}
                    </a>
                  </td>
                  <td className="px-4 py-2">{r.timestamp}</td>
                  <td className="px-4 py-2 text-center">
                    {badge(r.critical, "critical")}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {badge(r.high, "high")}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {badge(r.medium, "medium")}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {badge(r.low, "low")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {reports.length > 0 && (
        <div className="flex justify-between items-center mt-4">
          <div>
            <span className="text-gray-900 dark:text-white">
              Rows per page:
            </span>
            <select
              value={pageSize}
              onChange={(e) => {
                searchParams.set("pageSize", e.target.value);
                searchParams.set("page", "1");
                setSearchParams(searchParams);
              }}
              className="ml-2 border rounded p-1 text-black dark:text-white bg-white dark:bg-gray-800"
            >
              {[10, 25, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <div className="space-x-2">
            <button
              onClick={() => {
                const p = Math.max(page - 1, 1);
                searchParams.set("page", String(p));
                setSearchParams(searchParams);
              }}
              disabled={page <= 1}
              className="px-3 py-1 border rounded disabled:opacity-50 text-gray-900 dark:text-white"
            >
              Previous
            </button>
            <span className="text-gray-900 dark:text-white">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => {
                if (page < totalPages) {
                  searchParams.set("page", String(page + 1));
                  setSearchParams(searchParams);
                }
              }}
              disabled={page >= totalPages}
              className="px-3 py-1 border rounded disabled:opacity-50 text-gray-900 dark:text-white"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
