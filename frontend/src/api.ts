export async function fetchReports(params = {}) {
  const query = new URLSearchParams(
    params as Record<string, string>,
  ).toString();
  const res = await fetch(`/api/reports?${query}`);
  if (!res.ok) throw new Error("Failed to fetch reports");
  return res.json();
}
