import { useSettingsStore } from "@/stores/settingsStore";

const API_BASE_URL = "http://localhost:8000";

const getHeaders = () => {
  const apiKey = useSettingsStore.getState().apiKey;
  const headers: Record<string, string> = {};
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  return headers;
};

export const testApiKey = async (apiKey?: string): Promise<any> => {
  const headers = apiKey ? { "X-API-Key": apiKey } : getHeaders();
  const response = await fetch(`${API_BASE_URL}/api/test-key`, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Key Test Failed: ${errorText}`);
  }

  return response.json();
};

export const analyzeVideo = async (file: File): Promise<any> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: getHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Analyze Failed: ${errorText}`);
  }

  return response.json();
};

const downloadFile = async (endpoint: string, resultData: any, filename: string) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      ...getHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(resultData),
  });

  if (!response.ok) {
    throw new Error(`Export failed: ${await response.text()}`);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

export const exportFCPXML = (data: any) => downloadFile("/api/export/fcpxml", data, "project.fcpxml");
export const exportPremiere = (data: any) => downloadFile("/api/export/premiere", data, "project.xml");
export const exportSRT = (data: any) => downloadFile("/api/export/srt", data, "subtitles.srt");
export const exportZip = (data: any) => downloadFile("/api/export/zip", data, "scene-spark-export.zip");

export const renderShort = async (file: File, analysisJson: any): Promise<Blob> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("analysis", JSON.stringify(analysisJson));

  const response = await fetch(`${API_BASE_URL}/api/render`, {
    method: "POST",
    headers: getHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Rendering Failed: ${errorText}`);
  }

  return response.blob();
};
