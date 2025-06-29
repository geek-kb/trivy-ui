// File: frontend/src/components/ReportDetail.tsx

import {useEffect, useMemo, useState} from "react";
import {useParams, useSearchParams} from "react-router-dom";
import LoadingSpinner from "./LoadingSpinner";
import {PieChart, Pie, Cell, Tooltip, ResponsiveContainer} from "recharts";
import "./Chart.css";

const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"];
const COLORS: Record<string, string> = {
  CRITICAL: "#DC2626",
  HIGH: "#EA580C",
  MEDIUM: "#FBC02D",
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

export default function ReportDetail() {
  const {id} = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedSeverities, setSelectedSeverities] = useState<string[]>(() => {
    const sev = searchParams.getAll("severity");
    return sev.length > 0 ? sev : [...SEVERITIES];
  });
  const [pkgFilter, setPkgFilter] = useState(
    () => searchParams.get("pkgName") || "",
  );
  const [cveFilter, setCveFilter] = useState(
    () => searchParams.get("vulnId") || "",
  );
  const [sortBy, setSortBy] = useState<"Severity" | "Target" | "Package">(
    "Severity",
  );
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState(
    () => Number(searchParams.get("page")) || 1,
  );
  const [pageSize, setPageSize] = useState(
    () => Number(searchParams.get("pageSize")) || 10,
  );

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      selectedSeverities.forEach((s) => params.append("severity", s));
      if (pkgFilter) params.set("pkgName", pkgFilter);
      if (cveFilter) params.set("vulnId", cveFilter);
      params.set("page", String(currentPage));
      params.set("pageSize", String(pageSize));
      setSearchParams(params);

      const res = await fetch(`/api/report/${id}?${params.toString()}`);
      if (!res.ok) {
        if (res.status === 404) throw new Error("Report not found");
        throw new Error("Failed to fetch report");
      }
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      console.error("Fetch error:", err);
      setError(err.message || "Failed to load report.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, selectedSeverities, currentPage, pageSize]);

  const allVulns = useMemo(() => {
    if (!data) return [];
    const list: any[] = [];
    data.results.forEach((r: any) => {
      r.Vulnerabilities.forEach((v: any) => {
        list.push({
          target: r.Target,
          id: v.VulnerabilityID,
          pkg: v.PkgName,
          severity: v.Severity.toUpperCase(),
        });
      });
    });
    return list
      .filter((v) => selectedSeverities.includes(v.severity))
      .filter((v) =>
        pkgFilter
          ? v.pkg.toLowerCase().includes(pkgFilter.toLowerCase())
          : true,
      )
      .filter((v) =>
        cveFilter ? v.id.toLowerCase().includes(cveFilter.toLowerCase()) : true,
      )
      .sort((a, b) => {
        if (sortBy === "Severity") {
          return sortDir === "asc"
            ? SEVERITIES.indexOf(a.severity) - SEVERITIES.indexOf(b.severity)
            : SEVERITIES.indexOf(b.severity) - SEVERITIES.indexOf(a.severity);
        }
        const A = a[sortBy.toLowerCase() as keyof typeof a];
        const B = b[sortBy.toLowerCase() as keyof typeof b];
        return sortDir === "asc"
          ? String(A).localeCompare(String(B))
          : String(B).localeCompare(String(A));
      });
  }, [data, selectedSeverities, pkgFilter, cveFilter, sortBy, sortDir]);

  const paginated = allVulns.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );
  const totalPages = Math.max(Math.ceil(allVulns.length / pageSize), 1);

  const summaryData = SEVERITIES.map((s) => ({
    name: s,
    value: data?.summary[s.toLowerCase()] || 0,
  }));

  const handleSeverityClick = (severity: string) => {
    if (!SEVERITIES.includes(severity)) return;
    setSelectedSeverities([severity]);
    setCurrentPage(1);
  };

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="flex flex-col items-center justify-center mt-20 text-center">
        <p className="text-red-500 mb-4">{error}</p>
        <button
          onClick={fetchReport}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">{data.artifact}</h1>

      {summaryData.reduce((acc, cur) => acc + cur.value, 0) > 0 ? (
        <div className="w-full h-72 mb-6">
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={summaryData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({cx, cy, midAngle, outerRadius, index, value}) => {
                  if (index === undefined || !summaryData[index]) return null;
                  const severity = summaryData[index].name;

                  const RADIAN = Math.PI / 180;
                  const radius = outerRadius + 20;
                  const angle = midAngle;
                  const x = cx + radius * Math.cos(-angle * RADIAN);
                  const y = cy + radius * Math.sin(-angle * RADIAN);

                  let finalX = x;
                  let finalY = y;
                  let textAnchor: "start" | "middle" | "end" = "middle";

                  if (angle > 75 && angle < 105) {
                    finalY += -9;
                    textAnchor = "middle";
                  } else if (angle > 240 && angle < 300) {
                    finalY += 9;
                    textAnchor = "middle";
                  } else if ((angle >= 0 && angle <= 45) || angle >= 315) {
                    finalX += 3;
                    textAnchor = "start";
                  } else if (angle >= 135 && angle <= 225) {
                    finalX -= 3;
                    textAnchor = "end";
                  } else {
                    textAnchor = finalX > cx ? "start" : "end";
                  }

                  return (
                    <text
                      x={finalX}
                      y={finalY}
                      textAnchor={textAnchor}
                      dominantBaseline="central"
                      fill={COLORS[severity]}
                      fontSize={16}
                      style={{cursor: "pointer"}}
                      onClick={() => handleSeverityClick(severity)}
                    >
                      {value}
                    </text>
                  );
                }}
              >
                {summaryData.map((entry, idx) => (
                  <Cell key={`cell-${idx}`} fill={COLORS[entry.name]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="text-center text-gray-400 mb-6">
          No vulnerabilities detected in this report.
        </div>
      )}

      {/* Severity Filters */}
      <div className="mb-4 flex flex-wrap gap-4">
        {["All", ...SEVERITIES].map((s) => (
          <label key={s} className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={
                s === "All"
                  ? selectedSeverities.length === SEVERITIES.length
                  : selectedSeverities.includes(s)
              }
              onChange={() => {
                setCurrentPage(1);
                if (s === "All") {
                  setSelectedSeverities((prev) =>
                    prev.length === SEVERITIES.length ? [] : [...SEVERITIES],
                  );
                } else {
                  setSelectedSeverities((prev) =>
                    prev.includes(s)
                      ? prev.filter((x) => x !== s)
                      : [...prev, s],
                  );
                }
              }}
              className="form-checkbox"
            />
            <span
              className={
                s === "All" ? "text-black dark:text-white" : SEVERITY_CLASSES[s]
              }
            >
              {s}
            </span>
          </label>
        ))}
      </div>

      {/* Text Filters */}
      <form
        onSubmit={(e) => e.preventDefault()}
        className="flex space-x-2 mb-4"
      >
        <input
          type="text"
          placeholder="Filter package"
          value={pkgFilter}
          onChange={(e) => {
            setPkgFilter(e.target.value);
            setCurrentPage(1);
          }}
          className="border px-3 py-2 rounded text-black"
        />
        <input
          type="text"
          placeholder="Filter CVE"
          value={cveFilter}
          onChange={(e) => {
            setCveFilter(e.target.value);
            setCurrentPage(1);
          }}
          className="border px-3 py-2 rounded text-black"
        />
      </form>

      {/* Table */}
      <table className="min-w-full divide-y divide-gray-700 mb-4">
        <thead className="bg-[#1F2937] text-white">
          <tr>
            {["Target", "Vulnerability", "Package", "Severity"].map((col) => (
              <th
                key={col}
                onClick={() => {
                  setSortBy(col as any);
                  setSortDir((d) => (d === "asc" ? "desc" : "asc"));
                  setCurrentPage(1);
                }}
                className="px-4 py-2 text-left cursor-pointer"
              >
                {col} {sortBy === col && (sortDir === "asc" ? "↑" : "↓")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paginated.length === 0 ? (
            <tr>
              <td
                colSpan={4}
                className="text-center text-gray-400 px-4 py-6 italic"
              >
                No matching vulnerabilities
              </td>
            </tr>
          ) : (
            paginated.map((v, i) => (
              <tr
                key={`${v.id}-${i}`}
                className="hover:bg-gray-700 hover:text-white"
              >
                <td className="px-4 py-2">{v.target}</td>
                <td className="px-4 py-2">
                  {v.id.startsWith("CVE-") ? (
                    <a
                      href={`https://cve.mitre.org/cgi-bin/cvename.cgi?name=${v.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline"
                    >
                      {v.id}
                    </a>
                  ) : (
                    v.id
                  )}
                </td>
                <td className="px-4 py-2">{v.pkg}</td>
                <td
                  className={`px-4 py-2 font-semibold ${SEVERITY_CLASSES[v.severity]}`}
                >
                  {v.severity}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Pagination */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="border rounded px-2 py-1 text-black"
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
            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
            disabled={currentPage <= 1}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
            disabled={currentPage >= totalPages}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
