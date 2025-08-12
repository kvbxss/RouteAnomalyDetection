export const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function getJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function postJSON<T>(
  path: string,
  body: unknown,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    ...init,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadCSV(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/flights/upload_csv/`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function trainModel(opts: {
  contamination?: number;
  flight_limit?: number;
  save_model?: boolean;
}) {
  return postJSON("/api/anomalies/train_model/", opts);
}

export function runDetection(opts: {
  flight_ids?: string[];
  retrain?: boolean;
}) {
  return postJSON("/api/anomalies/detect_anomalies/", opts);
}
