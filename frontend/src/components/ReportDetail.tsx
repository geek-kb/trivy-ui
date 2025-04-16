import {useEffect, useState} from "react";
import {useParams} from "react-router-dom";

type Vulnerability = {
  VulnerabilityID: string;
  PkgName: string;
  Severity: string;
};

function getSeverityColor(sev: string) {
  switch (sev.toUpperCase()) {
    case "CRITICAL":
      return "#B91C1C"; // Red
    case "HIGH":
      return "#D97706"; // Orange
    case "MEDIUM":
      return "#CA8A04"; // Yellow
    case "LOW":
      return "#2563EB"; // Blue
    case "UNKNOWN":
      return "#6B7280"; // Gray
    default:
      return "#000000";
  }
}

export default function ReportDetail() {
  const {id} = useParams();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch(`/api/report/${id}`)
      .then((res) => res.json())
      .then(setData);
  }, [id]);

  if (!data) return <p>Loading report...</p>;

  return (
    <div>
      <h2>Report: {data.artifact}</h2>
      <p>
        <strong>Total vulnerabilities:</strong> {data.summary.total}
      </p>
      {data.results.map((r: any, i: number) => (
        <div key={i} style={{marginBottom: "2rem"}}>
          <h3>{r.Target}</h3>
          <table style={{width: "100%", borderCollapse: "collapse"}}>
            <thead>
              <tr style={{textAlign: "left", borderBottom: "2px solid #ccc"}}>
                <th style={{padding: "8px"}}>Severity</th>
                <th style={{padding: "8px"}}>CVE</th>
                <th style={{padding: "8px"}}>Package</th>
              </tr>
            </thead>
            <tbody>
              {r.Vulnerabilities.map((v: Vulnerability, idx: number) => (
                <tr key={idx}>
                  <td
                    style={{
                      padding: "8px",
                      fontWeight: 600,
                      color: getSeverityColor(v.Severity),
                    }}
                  >
                    {v.Severity.toUpperCase()}
                  </td>
                  <td style={{padding: "8px"}}>
                    <a
                      href={`https://cve.org/CVERecord?id=${v.VulnerabilityID}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {v.VulnerabilityID}
                    </a>
                  </td>
                  <td style={{padding: "8px", fontWeight: "bold"}}>
                    {v.PkgName}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
