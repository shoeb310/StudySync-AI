"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  IconButton,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Paper,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Tooltip,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import SearchIcon from "@mui/icons-material/Search";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";
import AutoStoriesOutlinedIcon from "@mui/icons-material/AutoStoriesOutlined";
import { fetchDocumentContent } from "../services/api";
import { DocumentContentResponse, DocumentChunkDetail } from "../types";

interface DocumentReaderDialogProps {
  open: boolean;
  onClose: () => void;
  notebookId: string;
  filename: string;
}

export default function DocumentReaderDialog({
  open,
  onClose,
  notebookId,
  filename,
}: DocumentReaderDialogProps) {
  const [data, setData] = useState<DocumentContentResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedPageTab, setSelectedPageTab] = useState<number>(-1); // -1 = All Pages
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    if (open && notebookId && filename) {
      loadContent();
    } else {
      setData(null);
      setError("");
      setSearchQuery("");
      setSelectedPageTab(-1);
    }
  }, [open, notebookId, filename]);

  const loadContent = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await fetchDocumentContent(notebookId, filename);
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load document content.");
    } finally {
      setLoading(false);
    }
  };

  // Group chunks by page number
  const pageNumbers = useMemo(() => {
    if (!data?.chunks) return [];
    const pages = Array.from(new Set(data.chunks.map((c) => c.page_number)));
    return pages.sort((a, b) => a - b);
  }, [data]);

  // Filter chunks by page and search term
  const filteredChunks = useMemo(() => {
    if (!data?.chunks) return [];
    return data.chunks.filter((c) => {
      const matchPage = selectedPageTab === -1 || c.page_number === selectedPageTab;
      const matchQuery =
        !searchQuery.trim() ||
        c.text.toLowerCase().includes(searchQuery.toLowerCase());
      return matchPage && matchQuery;
    });
  }, [data, selectedPageTab, searchQuery]);

  // Group filtered chunks by page
  const chunksByPage = useMemo(() => {
    const map = new Map<number, DocumentChunkDetail[]>();
    for (const chunk of filteredChunks) {
      if (!map.has(chunk.page_number)) {
        map.set(chunk.page_number, []);
      }
      map.get(chunk.page_number)!.push(chunk);
    }
    return map;
  }, [filteredChunks]);

  const handleCopyAll = () => {
    if (!data?.chunks) return;
    const textToCopy = filteredChunks.map((c) => c.text).join("\n\n");
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          backgroundColor: "background.paper",
          backgroundImage: "none",
          border: "1px solid",
          borderColor: "divider",
          height: { xs: "90vh", sm: "85vh" },
          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      {/* Dialog Header */}
      <DialogTitle
        sx={{
          p: 2.5,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, overflow: "hidden" }}>
          <AutoStoriesOutlinedIcon sx={{ color: "primary.main", fontSize: 28 }} />
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="h6" noWrap sx={{ fontSize: "1.1rem", fontWeight: 600 }}>
              {filename}
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                Notebook: <b>{notebookId}</b>
              </Typography>
              {data && (
                <>
                  <Chip
                    label={`${data.total_pages} ${data.total_pages === 1 ? "page" : "pages"}`}
                    size="small"
                    variant="outlined"
                    sx={{ height: 20, fontSize: "0.7rem" }}
                  />
                  <Chip
                    label={`${data.total_chunks} chunks`}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ height: 20, fontSize: "0.7rem" }}
                  />
                </>
              )}
            </Box>
          </Box>
        </Box>

        <IconButton size="small" onClick={onClose} sx={{ color: "text.secondary" }}>
          <CloseIcon sx={{ fontSize: 20 }} />
        </IconButton>
      </DialogTitle>

      {/* Control Bar: Search & Page Selector */}
      {data && (
        <Box
          sx={{
            px: 2.5,
            py: 1.5,
            backgroundColor: "rgba(148, 163, 184, 0.04)",
            borderBottom: "1px solid",
            borderColor: "divider",
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            alignItems: { sm: "center" },
            gap: 1.5,
            justifyContent: "space-between",
          }}
        >
          {/* Search Filter */}
          <TextField
            size="small"
            placeholder="Search text in document..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ fontSize: 18, color: "text.secondary" }} />
                </InputAdornment>
              ),
              sx: { fontSize: "0.85rem", height: 36, width: { xs: "100%", sm: 260 } },
            }}
          />

          {/* Page Tabs */}
          {pageNumbers.length > 1 && (
            <Tabs
              value={selectedPageTab}
              onChange={(_, val) => setSelectedPageTab(val)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ minHeight: 36, "& .MuiTab-root": { minHeight: 36, py: 0.5, px: 1.5, fontSize: "0.8rem", textTransform: "none" } }}
            >
              <Tab label="All Pages" value={-1} />
              {pageNumbers.map((p) => (
                <Tab key={p} label={`Page ${p}`} value={p} />
              ))}
            </Tabs>
          )}

          {/* Copy Button */}
          <Tooltip title={copied ? "Copied!" : "Copy visible text"}>
            <Button
              size="small"
              variant="outlined"
              onClick={handleCopyAll}
              startIcon={copied ? <CheckIcon sx={{ fontSize: 16 }} /> : <ContentCopyIcon sx={{ fontSize: 16 }} />}
              sx={{ textTransform: "none", fontSize: "0.8rem", height: 34, flexShrink: 0 }}
            >
              {copied ? "Copied" : "Copy Text"}
            </Button>
          </Tooltip>
        </Box>
      )}

      {/* Main Document Content */}
      <DialogContent sx={{ p: 3, flexGrow: 1, overflowY: "auto" }}>
        {loading && (
          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", py: 8, gap: 2 }}>
            <CircularProgress size={36} />
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              Reconstructing document pages from vector store...
            </Typography>
          </Box>
        )}

        {error && (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={loadContent}>
                Retry
              </Button>
            }
          >
            {error}
          </Alert>
        )}

        {!loading && !error && data && filteredChunks.length === 0 && (
          <Box sx={{ textAlign: "center", py: 8 }}>
            <DescriptionOutlinedIcon sx={{ fontSize: 48, color: "text.secondary", opacity: 0.5, mb: 1 }} />
            <Typography variant="body1" sx={{ color: "text.secondary" }}>
              No text chunks found matching "{searchQuery}".
            </Typography>
          </Box>
        )}

        {!loading && !error && data && Array.from(chunksByPage.entries()).map(([pageNum, chunks]) => (
          <Box key={pageNum} sx={{ mb: 4 }}>
            {/* Page Header Indicator */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1.5 }}>
              <Chip
                label={`Page ${pageNum}`}
                color="primary"
                size="small"
                sx={{ fontWeight: 600, fontSize: "0.75rem" }}
              />
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                {chunks.length} {chunks.length === 1 ? "chunk" : "chunks"}
              </Typography>
              <Box sx={{ flexGrow: 1, height: "1px", backgroundColor: "divider" }} />
            </Box>

            {/* Page Content Card */}
            <Paper
              elevation={0}
              sx={{
                p: 3,
                backgroundColor: "rgba(148, 163, 184, 0.03)",
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 2.5,
              }}
            >
              {chunks.map((chunk, cIdx) => (
                <Box key={chunk.chunk_id} sx={{ mb: cIdx < chunks.length - 1 ? 2.5 : 0 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      lineHeight: 1.8,
                      fontSize: "0.925rem",
                      color: "text.primary",
                      whiteSpace: "pre-wrap",
                      fontFamily: "inherit",
                    }}
                  >
                    {chunk.text}
                  </Typography>
                  {cIdx < chunks.length - 1 && (
                    <Box
                      sx={{
                        my: 2,
                        borderBottom: "1px dashed",
                        borderColor: "rgba(148, 163, 184, 0.2)",
                      }}
                    />
                  )}
                </Box>
              ))}
            </Paper>
          </Box>
        ))}
      </DialogContent>

      {/* Dialog Footer */}
      <DialogActions
        sx={{
          p: 2,
          borderTop: "1px solid",
          borderColor: "divider",
          justifyContent: "space-between",
        }}
      >
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          {filteredChunks.length} chunks displayed
        </Typography>
        <Button onClick={onClose} variant="outlined" size="small" sx={{ textTransform: "none" }}>
          Close Reader
        </Button>
      </DialogActions>
    </Dialog>
  );
}
