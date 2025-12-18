"use client";

import React, { useState } from "react";
import {
  Box,
  Typography,
  Button,
  List,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Divider,
  Tooltip,
} from "@mui/material";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { NotebookSummary } from "../types";

interface NotebookManagerProps {
  notebooks: NotebookSummary[];
  activeNotebookId: string;
  onSelectNotebook: (id: string) => void;
  onCreateNotebook: (id: string) => void;
  onDeleteNotebook: (id: string) => void;
  loading?: boolean;
}

export default function NotebookManager({
  notebooks,
  activeNotebookId,
  onSelectNotebook,
  onCreateNotebook,
  onDeleteNotebook,
}: NotebookManagerProps) {
  const [openDialog, setOpenDialog] = useState(false);
  const [newNotebookId, setNewNotebookId] = useState("");
  const [dialogError, setDialogError] = useState("");

  const handleCreate = () => {
    const trimmed = newNotebookId.trim().toLowerCase().replace(/\s+/g, "-");
    if (!trimmed) {
      setDialogError("Please provide a valid notebook name.");
      return;
    }
    onCreateNotebook(trimmed);
    setNewNotebookId("");
    setDialogError("");
    setOpenDialog(false);
  };

  return (
    <Box
      sx={{
        width: 280,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid",
        borderColor: "divider",
        backgroundColor: "background.paper",
      }}
    >
      {/* Brand Header */}
      <Box sx={{ p: 2.5, display: "flex", alignItems: "center", gap: 1.5 }}>
        <Box
          sx={{
            width: 36,
            height: 36,
            borderRadius: "10px",
            background: "linear-gradient(135deg, #6366f1 0%, #38bdf8 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#ffffff",
          }}
        >
          <AutoAwesomeIcon sx={{ fontSize: 20 }} />
        </Box>
        <Box>
          <Typography variant="h6" sx={{ fontSize: "1.1rem", lineHeight: 1.2 }}>
            StudySync AI
          </Typography>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            Academic RAG Workspace
          </Typography>
        </Box>
      </Box>

      <Divider />

      {/* Action Bar */}
      <Box sx={{ p: 2, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Typography variant="subtitle2" sx={{ color: "text.secondary", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>
          Study Notebooks
        </Typography>
        <Button
          size="small"
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
          sx={{ fontSize: "0.8rem", py: 0.5, px: 1.5 }}
        >
          New
        </Button>
      </Box>

      {/* Notebooks List */}
      <Box sx={{ flexGrow: 1, overflowY: "auto", px: 1 }}>
        <List disablePadding>
          {notebooks.length === 0 ? (
            <Box sx={{ p: 3, textAlign: "center" }}>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                No notebooks created yet. Click <b>New</b> to start.
              </Typography>
            </Box>
          ) : (
            notebooks.map((nb) => {
              const isSelected = nb.notebook_id === activeNotebookId;
              return (
                <ListItemButton
                  key={nb.notebook_id}
                  selected={isSelected}
                  onClick={() => onSelectNotebook(nb.notebook_id)}
                  sx={{
                    borderRadius: 2,
                    mb: 0.5,
                    px: 1.5,
                    py: 1,
                    transition: "all 0.15s ease-in-out",
                    "&.Mui-selected": {
                      backgroundColor: "rgba(99, 102, 241, 0.15)",
                      border: "1px solid rgba(99, 102, 241, 0.3)",
                      "&:hover": {
                        backgroundColor: "rgba(99, 102, 241, 0.22)",
                      },
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 32, color: isSelected ? "primary.main" : "text.secondary" }}>
                    <MenuBookIcon sx={{ fontSize: 18 }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={nb.notebook_id}
                    primaryTypographyProps={{
                      fontSize: "0.875rem",
                      fontWeight: isSelected ? 600 : 400,
                      noWrap: true,
                    }}
                  />
                  <Chip
                    label={`${nb.document_count} docs`}
                    size="small"
                    sx={{
                      height: 20,
                      fontSize: "0.7rem",
                      mr: 0.5,
                      backgroundColor: isSelected ? "rgba(99, 102, 241, 0.25)" : "rgba(148, 163, 184, 0.1)",
                    }}
                  />
                  <Tooltip title="Clear notebook documents">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteNotebook(nb.notebook_id);
                      }}
                      sx={{ color: "text.secondary", "&:hover": { color: "error.main" } }}
                    >
                      <DeleteOutlineIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Tooltip>
                </ListItemButton>
              );
            })
          )}
        </List>
      </Box>

      {/* Dialog for creating a new notebook */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>Create New Notebook</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
            Organize documents under a specific course or topic identifier (e.g. <code>cs-101</code>, <code>biology-exam</code>).
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label="Notebook ID"
            placeholder="e.g. computer-networks"
            value={newNotebookId}
            onChange={(e) => setNewNotebookId(e.target.value)}
            error={Boolean(dialogError)}
            helperText={dialogError}
            variant="outlined"
            size="small"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
            }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setOpenDialog(false)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleCreate} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
