// frontend/src/components/ReportsList.tsx
import {useEffect, useState} from "react";

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

  const fetchReports = async () => {
    const res = await fetch(`/api/reports?artifact=${artifactFilter}`);
    const data = await res.json();
    setReports(data.results || []);
  };

  useEffect(() => {
    fetchReports();
  }, []);

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
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-300">
                Artifact
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-300">
                Timestamp
              </th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600 dark:text-gray-300">
                Critical
              </th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600 dark:text-gray-300">
                High
              </th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600 dark:text-gray-300">
                Medium
              </th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600 dark:text-gray-300">
                Low
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 text-sm text-gray-800 dark:text-gray-200">
            {reports.map((r) => (
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
    </section>
  );
}
