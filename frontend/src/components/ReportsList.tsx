import {useEffect, useState} from "react";
import {fetchReports} from "../api";

type Report = {
  id: string;
  artifact: string;
  timestamp: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
};

export default function ReportsList() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  const [artifact, setArtifact] = useState("");
  const [minHigh, setMinHigh] = useState(0);

  const loadReports = () => {
    setLoading(true);
    fetchReports({
      artifact,
      min_high: minHigh.toString(),
    })
      .then((data) => {
        setReports(data.results);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadReports();
  }, []);

  return (
    <div>
      <div style={{marginBottom: "1rem"}}>
        <input
          placeholder="Search by artifact"
          value={artifact}
          onChange={(e) => setArtifact(e.target.value)}
        />
        <input
          type="number"
          placeholder="Min HIGH"
          value={minHigh}
          onChange={(e) => setMinHigh(Number(e.target.value))}
          style={{marginLeft: "1rem"}}
        />
        <button onClick={loadReports} style={{marginLeft: "1rem"}}>
          Apply Filters
        </button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Artifact</th>
              <th>Timestamp</th>
              <th>Critical</th>
              <th>High</th>
              <th>Medium</th>
              <th>Low</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td>
                  <a href={`/report/${report.id}`}>{report.artifact}</a>
                </td>
                <td>{new Date(report.timestamp).toLocaleString()}</td>
                <td>{report.critical}</td>
                <td>{report.high}</td>
                <td>{report.medium}</td>
                <td>{report.low}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
