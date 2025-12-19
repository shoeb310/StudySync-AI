"use client";

import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  AppBar,
  Toolbar,
  Chip,
  Tabs,
  Tab,
  CircularProgress,
  IconButton,
  Tooltip,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import NotebookManager from "../components/NotebookManager";
import DocumentUpload from "../components/DocumentUpload";
import ChatWindow from "../components/ChatWindow";
import CitationDrawer from "../components/CitationDrawer";
import DocumentReaderDialog from "../components/DocumentReaderDialog";
import { fetchNotebooks, deleteNotebook } from "../services/api";
import { NotebookSummary, CitationSource } from "../types";

export default function StudyWorkspace() {
  const [notebooks, setNotebooks] = useState<NotebookSummary[]>([]);
  const [activeNotebookId, setActiveNotebookId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  // Citation Drawer state
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<CitationSource | null>(null);
  const [activeCitations, setActiveCitations] = useState<CitationSource[]>([]);

  // Document Reader Dialog state
  const [readerOpen, setReaderOpen] = useState<boolean>(false);
  const [readingDocName, setReadingDocName] = useState<string>("");

  const loadNotebooks = async () => {
    try {
      setLoading(true);
      const data = await fetchNotebooks();
      setNotebooks(data);

      // Auto-select first notebook if none selected
      if (!activeNotebookId && data.length > 0) {
        setActiveNotebookId(data[0].notebook_id);
      }
    } catch (err) {
      console.error("Failed to load notebooks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotebooks();
  }, []);

  const handleCreateNotebook = (id: string) => {
    const exists = notebooks.some((n) => n.notebook_id === id);
    if (!exists) {
      const newNb: NotebookSummary = {
        notebook_id: id,
        document_count: 0,
        chunk_count: 0,
        documents: [],
      };
      setNotebooks((prev) => [...prev, newNb]);
    }
    setActiveNotebookId(id);
  };

  const handleDeleteNotebook = async (id: string) => {
    try {
      await deleteNotebook(id);
      setNotebooks((prev) => prev.filter((n) => n.notebook_id !== id));
      if (activeNotebookId === id) {
        const remaining = notebooks.filter((n) => n.notebook_id !== id);
        setActiveNotebookId(remaining.length > 0 ? remaining[0].notebook_id : "");
      }
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleOpenCitation = (citation: CitationSource, allCitations: CitationSource[]) => {
    setSelectedCitation(citation);
    setActiveCitations(allCitations);
    setDrawerOpen(true);
  };

  const handleReadDocument = (filename: string) => {
    setReadingDocName(filename);
    setReaderOpen(true);
  };

  const activeNotebook = notebooks.find((n) => n.notebook_id === activeNotebookId);

  return (
    <Box sx={{ display: "flex", height: "100vh", width: "100vw", backgroundColor: "background.default" }}>
      {/* Sidebar: Notebook Manager */}
      <NotebookManager
        notebooks={notebooks}
        activeNotebookId={activeNotebookId}
        onSelectNotebook={(id) => setActiveNotebookId(id)}
        onCreateNotebook={handleCreateNotebook}
        onDeleteNotebook={handleDeleteNotebook}
        loading={loading}
      />

      {/* Main Content Workspace */}
      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
        {/* Top Navbar */}
        <AppBar position="static" elevation={0} sx={{ backgroundColor: "background.paper", borderBottom: "1px solid", borderColor: "divider" }}>
          <Toolbar sx={{ justifyContent: "space-between", minHeight: "64px !important" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
              <Typography variant="h6" sx={{ fontSize: "1rem" }}>
                {activeNotebookId ? `Notebook: ${activeNotebookId}` : "Select or Create a Notebook"}
              </Typography>
              {activeNotebook && (
                <Chip
                  label={`${activeNotebook.chunk_count} chunks indexed`}
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ fontSize: "0.75rem" }}
                />
              )}
            </Box>

            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <Tabs
                value={activeTab}
                onChange={(_, newVal) => setActiveTab(newVal)}
                textColor="primary"
                indicatorColor="primary"
                sx={{ minHeight: "48px" }}
              >
                <Tab icon={<UploadFileIcon sx={{ fontSize: 18 }} />} iconPosition="start" label="Upload Materials" sx={{ minHeight: "48px", textTransform: "none", fontSize: "0.85rem" }} />
                <Tab icon={<ChatBubbleOutlineIcon sx={{ fontSize: 18 }} />} iconPosition="start" label="Academic Chat" sx={{ minHeight: "48px", textTransform: "none", fontSize: "0.85rem" }} />
              </Tabs>

              <Tooltip title="Refresh notebooks">
                <IconButton size="small" onClick={loadNotebooks} sx={{ color: "text.secondary" }}>
                  {loading ? <CircularProgress size={18} /> : <RefreshIcon sx={{ fontSize: 20 }} />}
                </IconButton>
              </Tooltip>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Tab Panel Area */}
        <Box sx={{ flexGrow: 1, overflow: "hidden", display: "flex" }}>
          {activeTab === 0 ? (
            <Box sx={{ flexGrow: 1, overflowY: "auto" }}>
              <DocumentUpload
                activeNotebookId={activeNotebookId}
                indexedDocuments={activeNotebook?.documents || []}
                onUploadSuccess={() => {
                  loadNotebooks();
                }}
              />
            </Box>
          ) : (
            <ChatWindow
              activeNotebookId={activeNotebookId}
              onOpenCitation={handleOpenCitation}
            />
          )}
        </Box>
      </Box>

      {/* Slide-out Source Citation Drawer */}
      <CitationDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        selectedCitation={selectedCitation}
        allCitations={activeCitations}
        onSelectCitation={(c) => setSelectedCitation(c)}
        onReadDocument={handleReadDocument}
      />

      {/* Workspace Document Reader Dialog */}
      <DocumentReaderDialog
        open={readerOpen}
        onClose={() => setReaderOpen(false)}
        notebookId={activeNotebookId}
        filename={readingDocName}
      />
    </Box>
  );
}
