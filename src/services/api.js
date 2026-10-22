// CLAUSENT API Service Client

const API_BASE = import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? "http://127.0.0.1:8000/api" : "/api");

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (err) {
    console.warn("Backend not reachable or offline:", err);
    return null;
  }
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || errData.message || "Failed to upload document.");
  }
  return await res.json();
}

export async function startAnalysis(documentId, targetLanguage = "English", sourceLanguage = "Auto detect") {
  const params = new URLSearchParams({
    target_language: targetLanguage,
    source_language: sourceLanguage,
  });

  const res = await fetch(`${API_BASE}/analysis/${documentId}/start?${params.toString()}`, {
    method: "POST",
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || errData.message || "Failed to start analysis.");
  }
  return await res.json();
}

export async function getAnalysisStatus(id) {
  const res = await fetch(`${API_BASE}/analysis/${id}/status`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || errData.message || "Failed to get analysis status.");
  }
  return await res.json();
}

export async function getAnalysisResults(id) {
  const res = await fetch(`${API_BASE}/analysis/${id}/results`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || errData.message || "Failed to get analysis results.");
  }
  return await res.json();
}

export async function getClauses(analysisId, riskFilter = "all") {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/clauses?risk=${encodeURIComponent(riskFilter)}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to get clauses.");
  }
  return await res.json();
}

export async function getClauseDetail(analysisId, clauseId) {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/clauses/${clauseId}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to get clause detail.");
  }
  return await res.json();
}

export async function explainClause(analysisId, clauseId, preferredLanguage = "English", forceLlm = true) {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/clauses/${clauseId}/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      preferred_language: preferredLanguage,
      force_llm: forceLlm,
    }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to generate detailed explanation.");
  }
  return await res.json();
}

export async function listDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) {
    throw new Error("Failed to load documents list.");
  }
  return await res.json();
}

export async function deleteDocument(docId) {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error("Failed to delete document.");
  }
  return await res.json();
}

export async function translateAnalysis(id, targetLanguage = "English") {
  const res = await fetch(`${API_BASE}/analysis/${id}/translate?target_language=${encodeURIComponent(targetLanguage)}`, {
    method: "POST",
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || errData.message || "Failed to translate analysis.");
  }
  return await res.json();
}

export function getPdfReportUrl(id, language = null) {
  if (language) {
    return `${API_BASE}/reports/${id}/pdf?language=${encodeURIComponent(language)}`;
  }
  return `${API_BASE}/reports/${id}/pdf`;
}

export function getJsonReportUrl(id) {
  return `${API_BASE}/reports/${id}/json`;
}

export function getCsvReportUrl(id) {
  return `${API_BASE}/reports/${id}/csv`;
}

