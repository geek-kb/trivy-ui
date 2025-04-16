// frontend/src/components/ReportDetail.tsx
import {useEffect, useMemo, useState} from "react";
import {useParams, useSearchParams} from "react-router-dom";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"];
const COLORS: Record<string, string> = {
  CRITICAL: "#DC2626",
  HIGH: "#EA580C",
  MEDIUM: "#D97706",
  LOW: "#2563EB",
  UNKNOWN: "#6B7280",
};
const SEVERITY_CLASSES: Record<string, string> = {
  CRITICAL: "text-red-600",
  HIGH: "text-orange-500",
  MEDIUM: "text-yellow-500",
  LOW: "text-blue-500",
  UNKNOWN: "text-gray-500",
};

export default function ReportDetail({
  enableSeverityFilter = false,
}: {
  enableSeverityFilter?: boolean;
}) {
  const {id} = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<any>(null);

  const [selectedSeverities, setSelectedSeverities] = useState<string[]>(
    () => searchParams.getAll("severity") || [...SEVERITIES],
  );
  const [pkgFilter, setPkgFilter] = useState(
    () => searchParams.get("pkgName") || "",
  );
  const [cveFilter, setCveFilter] = useState(
    () => searchParams.get("vulnId") || "",
  );

  const [sortBy, setSortBy] = useState("Severity");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState(
    () => Number(searchParams.get("page")) || 1,
  );
  const [pageSize, setPageSize] = useState(
    () => Number(searchParams.get("pageSize")) || 10,
  );

  useEffect(() => {
    const params = new URLSearchParams();
    selectedSeverities.forEach((s) => params.append("severity", s));
    if (pkgFilter) params.set("pkgName", pkgFilter);
    if (cveFilter) params.set("vulnId", cveFilter);
    params.set("page", String(currentPage));
    params.set("pageSize", String(pageSize));
    setSearchParams(params);

    fetch(`/api/report/${id}?${params.toString()}`)
      .then((res) => res.json())
      .then(setData);
  }, [id, selectedSeverities, pkgFilter, cveFilter, currentPage, pageSize]);

  const toggleSeverity = (sev: string) => {
    const next = selectedSeverities.includes(sev)
      ? selectedSeverities.filter((s) => s !== sev)
      : [...selectedSeverities, sev];
    setSelectedSeverities(next);
    setCurrentPage(1);
  };

  const resetFilters = () => {
    setSelectedSeverities([...SEVERITIES]);
    setPkgFilter("");
    setCveFilter("");
    setCurrentPage(1);
  };

  const sortedVulns = useMemo(() => {
    const vulns =
      data?.results.flatMap((r: any) =>
        (r.Vulnerabilities || []).map((v: any) => ({
          ...v,
          Target: r.Target,
        })),
      ) || [];

    return [...vulns].sort((a, b) => {
      const valA = a[sortBy] || "";
      const valB = b[sortBy] || "";
      return sortDir === "asc"
        ? valA.localeCompare(valB)
        : valB.localeCompare(valA);
    });
  }, [data, sortBy, sortDir]);

  const paginatedVulns = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedVulns.slice(start, start + pageSize);
  }, [sortedVulns, currentPage, pageSize]);

  if (!data) return <p>Loading report...</p>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Report: {data.artifact}</h2>

      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={SEVERITIES.map((s) => ({
              name: s,
              value: data.summary[s.toLowerCase()] || 0,
            }))}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            onClick={({name}) => {
              setSelectedSeverities([name]);
              setCurrentPage(1);
            }}
          >
            {SEVERITIES.map((s, i) => (
              <Cell key={i} fill={COLORS[s]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      {enableSeverityFilter && (
        <div className="mb-6 space-y-4">
          <div className="flex flex-wrap gap-2">
            {SEVERITIES.map((sev) => {
              const selected = selectedSeverities.includes(sev);
              return (
                <button
                  key={sev}
                  onClick={() => toggleSeverity(sev)}
                  style={{
                    backgroundColor: selected ? COLORS[sev] : "transparent",
                    color: selected ? "#fff" : "#4B5563",
                    border: `1px solid ${selected ? COLORS[sev] : "#D1D5DB"}`,
                  }}
                  className="px-3 py-1 text-sm rounded-full transition"
                >
                  {sev}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap gap-4 items-center">
            <input
              type="text"
              placeholder="Filter by package name..."
              className="border px-2 py-1 rounded text-sm text-black dark:text-white bg-white dark:bg-gray-800"
              value={pkgFilter}
              onChange={(e) => setPkgFilter(e.target.value)}
            />
            <input
              type="text"
              placeholder="Filter by CVE ID..."
              className="border px-2 py-1 rounded text-sm text-black dark:text-white bg-white dark:bg-gray-800"
              value={cveFilter}
              onChange={(e) => setCveFilter(e.target.value)}
            />
            <button
              onClick={resetFilters}
              className="text-sm text-blue-600 hover:underline"
            >
              Reset all filters
            </button>
          </div>
        </div>
      )}

      <table className="min-w-full border-collapse text-sm">
        <thead className="border-b">
          <tr className="text-left">
            {["Severity", "VulnerabilityID", "PkgName", "Target"].map((col) => (
              <th
                key={col}
                className="px-3 py-2 cursor-pointer"
                onClick={() => {
                  if (sortBy === col) {
                    setSortDir(sortDir === "asc" ? "desc" : "asc");
                  } else {
                    setSortBy(col);
                    setSortDir("asc");
                  }
                }}
              >
                {col}
                {sortBy === col ? (sortDir === "asc" ? " 🔼" : " 🔽") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paginatedVulns.length === 0 ? (
            <tr>
              <td
                colSpan={4}
                className="px-4 py-3 italic text-gray-500 text-center"
              >
                ✅ No vulnerabilities matched your filters.
              </td>
            </tr>
          ) : (
            paginatedVulns.map((v: any, i: number) => (
              <tr
                key={i}
                className={`border-t hover:bg-gray-50 dark:hover:bg-gray-700 ${
                  v.Severity === "CRITICAL"
                    ? "bg-red-50 dark:bg-red-900/20"
                    : ""
                }`}
              >
                <td
                  className={`px-3 py-2 font-semibold ${SEVERITY_CLASSES[v.Severity?.toUpperCase()] || ""}`}
                >
                  {v.Severity}
                </td>
                <td className="px-3 py-2">
                  <a
                    href={`https://cve.org/CVERecord?id=${v.VulnerabilityID}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {v.VulnerabilityID}
                  </a>
                </td>
                <td className="px-3 py-2 font-mono">{v.PkgName}</td>
                <td className="px-3 py-2">{v.Target}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      <div className="mt-4 flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-2">
          <label htmlFor="pageSize" className="text-sm">
            Rows per page:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="border px-2 py-1 rounded text-sm text-black dark:text-white bg-white dark:bg-gray-800"
          >
            {[10, 15, 25, 50].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {Math.ceil(sortedVulns.length / pageSize)}
          </span>
          <button
            onClick={() =>
              setCurrentPage((p) =>
                p < Math.ceil(sortedVulns.length / pageSize) ? p + 1 : p,
              )
            }
            disabled={currentPage >= Math.ceil(sortedVulns.length / pageSize)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
