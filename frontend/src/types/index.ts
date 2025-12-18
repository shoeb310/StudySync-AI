export interface NotebookSummary {
  notebook_id: string;
  document_count: number;
  chunk_count: number;
  documents: string[];
}

export interface NotebookListResponse {
  notebooks: NotebookSummary[];
}

export interface UploadResponse {
  status: string;
  notebook_id: string;
  filename: string;
  chunks_ingested: number;
  total_characters: number;
}

export interface DeleteResponse {
  status: string;
  notebook_id: string;
  message: string;
  deleted_chunks: number;
}

export interface CitationSource {
  doc_id: number;
  chunk_id: string;
  filename: string;
  page_number: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  citations?: CitationSource[];
  timestamp: string;
  isStreaming?: boolean;
}

export interface ChatStreamEvent {
  type: "content" | "citations" | "error";
  token?: string;
  citations?: CitationSource[];
  error?: string;
}
