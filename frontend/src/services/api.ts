import { NotebookSummary, NotebookListResponse, UploadResponse, DeleteResponse } from "../types";

let resolvedApiBase: string | null = null;

export async function getApiBaseUrl(): Promise<string> {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (resolvedApiBase) {
    return resolvedApiBase;
  }

  // Check both 8000 (standard local uvicorn) and 8001 (docker-compose)
  const candidates = [
    "http://localhost:8000/api/v1",
    "http://localhost:8001/api/v1",
    "http://127.0.0.1:8000/api/v1",
    "http://127.0.0.1:8001/api/v1",
  ];

  for (const candidate of candidates) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1200);
      const res = await fetch(`${candidate}/health`, {
        method: "GET",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (res.ok) {
        resolvedApiBase = candidate;
        return candidate;
      }
    } catch {
      // continue to next candidate
    }
  }

  // Default fallback to 8000
  return "http://localhost:8000/api/v1";
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchNotebooks(): Promise<NotebookSummary[]> {
  const apiBase = await getApiBaseUrl();
  try {
    const res = await fetch(`${apiBase}/notebooks`, { cache: "no-store" });
    if (!res.ok) {
      const errorText = await res.text();
      throw new ApiError(res.status, `Failed to load notebooks: ${errorText}`);
    }
    const data: NotebookListResponse = await res.json();
    return data.notebooks || [];
  } catch (err: any) {
    console.error("fetchNotebooks error:", err);
    throw new Error("Cannot connect to backend server. Make sure FastAPI is running (uvicorn app.main:app --reload --port 8000).");
  }
}

export async function uploadDocument(
  notebookId: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadResponse> {
  const apiBase = await getApiBaseUrl();

  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("notebook_id", notebookId);
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${apiBase}/upload`);

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res: UploadResponse = JSON.parse(xhr.responseText);
          resolve(res);
        } catch (e) {
          reject(new Error("Invalid server response format"));
        }
      } else {
        try {
          const errRes = JSON.parse(xhr.responseText);
          reject(new ApiError(xhr.status, errRes.detail || "Upload failed"));
        } catch {
          reject(new ApiError(xhr.status, xhr.statusText || "Upload failed"));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error("Cannot connect to backend server. Is FastAPI running on port 8000 or 8001?"));
    };

    xhr.send(formData);
  });
}

export async function deleteNotebook(notebookId: string): Promise<DeleteResponse> {
  const apiBase = await getApiBaseUrl();
  const res = await fetch(`${apiBase}/documents/${encodeURIComponent(notebookId)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new ApiError(res.status, `Failed to delete documents: ${errText}`);
  }
  return res.json();
}
