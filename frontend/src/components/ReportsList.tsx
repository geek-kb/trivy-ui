// frontend/src/components/ReportsList.tsx
import {useEffect, useState} from "react";
import {useSearchParams} from "react-router-dom";

type ReportSummary = {
  id: string;
  artifact: string;
  timestamp: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
};

export default function ReportsList() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [artifactFilter, setArtifactFilter] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();

  const sortField =
    (searchParams.get("sortField") as keyof ReportSummary) || "timestamp";
  const sortDir = (searchParams.get("sortDir") as "asc" | "desc") || "desc";
  const currentPage = Number(searchParams.get("page")) || 1;
  const pageSize = Number(searchParams.get("pageSize")) || 10;

  const fetchReports = async () => {
    const res = await fetch(`/api/reports?artifact=${artifactFilter}`);
    const data = await res.json();
    setReports(data.results || []);
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleSort = (field: keyof ReportSummary) => {
    const newDir =
      field === sortField ? (sortDir === "asc" ? "desc" : "asc") : "asc";
    searchParams.set("sortField", field);
    searchParams.set("sortDir", newDir);
    searchParams.set("page", "1");
    setSearchParams(searchParams);
  };

  const sortedReports = [...reports].sort((a, b) => {
    const aValue = a[sortField] ?? "";
    const bValue = b[sortField] ?? "";

    if (typeof aValue === "number" && typeof bValue === "number") {
      return sortDir === "asc" ? aValue - bValue : bValue - aValue;
    }
    return sortDir === "asc"
      ? String(aValue).localeCompare(String(bValue))
      : String(bValue).localeCompare(String(aValue));
  });

  const paginatedReports = sortedReports.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  const totalPages = Math.max(Math.ceil(sortedReports.length / pageSize), 1);

  const getBadgeColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: "bg-red-600 text-white",
      high: "bg-orange-500 text-white",
      medium: "bg-yellow-400 text-black",
      low: "bg-blue-400 text-white",
    };
    return `px-2 py-1 rounded text-xs font-semibold ${colors[severity] || "bg-gray-300"}`;
  };

  return (
    <section className="mt-10 space-y-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          fetchReports();
        }}
        className="flex flex-col md:flex-row gap-4 items-start md:items-end"
      >
        <div className="flex flex-col w-full md:w-1/3">
          <label className="text-sm text-gray-600 dark:text-gray-300 mb-1">
            Artifact Name
          </label>
          <input
            type="text"
            placeholder="Search by artifact"
            value={artifactFilter}
            onChange={(e) => setArtifactFilter(e.target.value)}
            className="border px-3 py-2 rounded shadow-sm focus:outline-none focus:ring focus:border-blue-300 text-black dark:text-white bg-white dark:bg-gray-800"
          />
        </div>

        <button
          type="submit"
          className="bg-blue-600 text-white px-5 py-2 rounded shadow hover:bg-blue-700 transition mt-2 md:mt-0"
        >
          Apply Filters
        </button>
      </form>

      <div className="overflow-auto rounded-lg shadow ring-1 ring-black ring-opacity-5">
        <table className="min-w-full divide-y divide-gray-200 bg-white dark:bg-gray-800">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              {[
                {label: "Artifact", field: "artifact"},
                {label: "Timestamp", field: "timestamp"},
                {label: "Critical", field: "critical"},
                {label: "High", field: "high"},
                {label: "Medium", field: "medium"},
                {label: "Low", field: "low"},
              ].map(({label, field}) => (
                <th
                  key={field}
                  onClick={() => handleSort(field as keyof ReportSummary)}
                  className={`px-4 py-3 ${
                    field === "artifact" || field === "timestamp"
                      ? "text-left"
                      : "text-center"
                  } text-sm font-semibold text-gray-600 dark:text-gray-300 cursor-pointer`}
                >
                  {label}
                  {sortField === field && (sortDir === "asc" ? " 🔼" : " 🔽")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 text-sm text-gray-800 dark:text-gray-200">
            {paginatedReports.map((r) => (
              <tr
                key={r.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <td className="px-4 py-3">
                  <a
                    href={`/report/${r.id}`}
                    className="text-blue-600 hover:underline font-medium"
                  >
                    {r.artifact}
                  </a>
                </td>
                <td className="px-4 py-3">{r.timestamp || "Invalid Date"}</td>
                <td className="px-4 py-3 text-center">
                  <span className={getBadgeColor("critical")}>
                    {r.critical}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={getBadgeColor("high")}>{r.high}</span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={getBadgeColor("medium")}>{r.medium}</span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={getBadgeColor("low")}>{r.low}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4">
        <div className="flex items-center gap-2">
          <label htmlFor="pageSize" className="text-sm">
            Rows per page:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => {
              searchParams.set("pageSize", e.target.value);
              searchParams.set("page", "1");
              setSearchParams(searchParams);
            }}
            className="border px-2 py-1 rounded text-sm text-black dark:text-white bg-white dark:bg-gray-800"
          >
            {[10, 20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              const prev = Math.max(currentPage - 1, 1);
              searchParams.set("page", prev.toString());
              setSearchParams(searchParams);
            }}
            disabled={currentPage <= 1}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => {
              if (currentPage < totalPages) {
                searchParams.set("page", (currentPage + 1).toString());
                setSearchParams(searchParams);
              }
            }}
            disabled={currentPage >= totalPages}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
