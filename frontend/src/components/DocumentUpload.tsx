"use client";

import React, { useState, useRef } from "react";
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from "@mui/material";
import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import { uploadDocument } from "../services/api";
import { UploadResponse } from "../types";

interface DocumentUploadProps {
  activeNotebookId: string;
  indexedDocuments?: string[];
  onUploadSuccess: (response: UploadResponse) => void;
}

export default function DocumentUpload({
  activeNotebookId,
  indexedDocuments = [],
  onUploadSuccess,
}: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!activeNotebookId) {
      setErrorMsg("Please select or create a notebook before uploading documents.");
      return;
    }

    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith(".pdf") && !lowerName.endsWith(".txt")) {
      setErrorMsg("Unsupported file type. Please upload a .pdf or .txt file.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const res = await uploadDocument(activeNotebookId, file, (percent) => {
        setUploadProgress(percent);
      });
      setSuccessMsg(`Ingested "${res.filename}" (${res.chunks_ingested} chunks, ${res.total_characters} characters).`);
      onUploadSuccess(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload and parse document.");
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: "auto" }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 0.5 }}>
          Knowledge Ingestion
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          Target Notebook: <b>{activeNotebookId || "None Selected"}</b>
        </Typography>
      </Box>

      {/* Drag & Drop Zone */}
      <Paper
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        sx={{
          p: 5,
          textAlign: "center",
          cursor: "pointer",
          border: "2px dashed",
          borderColor: isDragging ? "primary.main" : "divider",
          backgroundColor: isDragging ? "rgba(99, 102, 241, 0.05)" : "background.paper",
          borderRadius: 3,
          transition: "all 0.2s ease-in-out",
          "&:hover": {
            borderColor: "primary.light",
            backgroundColor: "rgba(99, 102, 241, 0.03)",
          },
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFile(e.target.files[0]);
            }
          }}
        />
        <CloudUploadOutlinedIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
        <Typography variant="h6" sx={{ fontSize: "1rem", mb: 0.5 }}>
          Drag & Drop PDF or TXT files here
        </Typography>
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          Files are parsed page-by-page, chunked into 500-char windows, and embedded with Google Gemini.
        </Typography>
      </Paper>

      {/* Progress Indicator */}
      {isUploading && (
        <Box sx={{ mt: 2 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              Processing & Generating Embeddings...
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 600 }}>
              {uploadProgress}%
            </Typography>
          </Box>
          <LinearProgress variant="determinate" value={uploadProgress} sx={{ borderRadius: 1, height: 6 }} />
        </Box>
      )}

      {/* Status Alerts */}
      {errorMsg && (
        <Alert severity="error" sx={{ mt: 2, borderRadius: 2 }} onClose={() => setErrorMsg("")}>
          {errorMsg}
        </Alert>
      )}
      {successMsg && (
        <Alert severity="success" sx={{ mt: 2, borderRadius: 2 }} onClose={() => setSuccessMsg("")}>
          {successMsg}
        </Alert>
      )}

      {/* Indexed Documents in Active Notebook */}
      {indexedDocuments.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="subtitle2" sx={{ color: "text.secondary", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em", mb: 1 }}>
            Indexed In This Notebook ({indexedDocuments.length})
          </Typography>
          <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
            <List disablePadding>
              {indexedDocuments.map((docName, idx) => (
                <React.Fragment key={docName}>
                  {idx > 0 && <Divider />}
                  <ListItem sx={{ py: 1.2, px: 2 }}>
                    <ListItemIcon sx={{ minWidth: 36, color: "primary.light" }}>
                      <DescriptionOutlinedIcon sx={{ fontSize: 20 }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={docName}
                      primaryTypographyProps={{ fontSize: "0.875rem", fontWeight: 500 }}
                    />
                    <CheckCircleOutlineIcon sx={{ color: "success.main", fontSize: 18 }} />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Box>
      )}
    </Box>
  );
}
