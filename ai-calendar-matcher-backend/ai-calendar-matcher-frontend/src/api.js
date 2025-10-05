// api helper class

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function suggest({ location, preferences, freeWindows }) {
  const res = await fetch(`${API}/ai/suggest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location, preferences, freeWindows }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
