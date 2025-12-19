"use client";

import React from "react";
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Divider,
  Paper,
  Chip,
  List,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Button,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import BookmarkBorderIcon from "@mui/icons-material/BookmarkBorder";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import AutoStoriesOutlinedIcon from "@mui/icons-material/AutoStoriesOutlined";
import { CitationSource } from "../types";

interface CitationDrawerProps {
  open: boolean;
  onClose: () => void;
  selectedCitation: CitationSource | null;
  allCitations?: CitationSource[];
  onSelectCitation?: (citation: CitationSource) => void;
  onReadDocument?: (filename: string) => void;
}

export default function CitationDrawer({
  open,
  onClose,
  selectedCitation,
  allCitations = [],
  onSelectCitation,
  onReadDocument,
}: CitationDrawerProps) {
  if (!selectedCitation && allCitations.length === 0) {
    return null;
  }

  const activeCitation = selectedCitation || allCitations[0] || null;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: "100%", sm: 420 },
          backgroundColor: "background.paper",
          backgroundImage: "none",
          borderLeft: "1px solid",
          borderColor: "divider",
          p: 0,
        },
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2.5, display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid", borderColor: "divider" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <BookmarkBorderIcon sx={{ color: "primary.main" }} />
          <Typography variant="h6" sx={{ fontSize: "1.05rem", fontWeight: 600 }}>
            Source Citation Inspector
          </Typography>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: "text.secondary" }}>
          <CloseIcon sx={{ fontSize: 20 }} />
        </IconButton>
      </Box>

      {/* Content Area */}
      <Box sx={{ p: 3, flexGrow: 1, overflowY: "auto" }}>
        {activeCitation ? (
          <>
            {/* Citation Meta Header */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
              <Chip
                label={`Doc ${activeCitation.doc_id}`}
                color="primary"
                size="small"
                sx={{ fontWeight: 600 }}
              />
              <Chip
                label={`Page ${activeCitation.page_number}`}
                variant="outlined"
                size="small"
              />
            </Box>

            {/* Document Info Card */}
            <Paper
              elevation={0}
              sx={{
                p: 2,
                mb: 3,
                backgroundColor: "rgba(148, 163, 184, 0.05)",
                borderRadius: 2,
                border: "1px solid rgba(148, 163, 184, 0.12)",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
                <DescriptionOutlinedIcon sx={{ color: "primary.light", fontSize: 22 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, wordBreak: "break-word" }}>
                  {activeCitation.filename}
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: "text.secondary", display: "block" }}>
                Vector Chunk ID: <code>{activeCitation.chunk_id}</code>
              </Typography>
              {onReadDocument && (
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<AutoStoriesOutlinedIcon sx={{ fontSize: 16 }} />}
                  onClick={() => onReadDocument(activeCitation.filename)}
                  sx={{
                    mt: 1.5,
                    textTransform: "none",
                    fontSize: "0.75rem",
                    py: 0.3,
                    borderRadius: 1.5,
                  }}
                >
                  Read Entire Document
                </Button>
              )}
            </Paper>

            {/* Source Text Snippet */}
            <Typography
              variant="subtitle2"
              sx={{
                color: "text.secondary",
                textTransform: "uppercase",
                fontSize: "0.75rem",
                letterSpacing: "0.05em",
                mb: 1,
              }}
            >
              Retrieved Academic Context
            </Typography>
            <Paper
              elevation={0}
              sx={{
                p: 2.5,
                backgroundColor: "rgba(99, 102, 241, 0.04)",
                border: "1px solid rgba(99, 102, 241, 0.2)",
                borderRadius: 2.5,
                lineHeight: 1.7,
                fontSize: "0.9rem",
                color: "text.primary",
                whiteSpace: "pre-wrap",
                fontFamily: "inherit",
              }}
            >
              "{activeCitation.snippet}"
            </Paper>
          </>
        ) : (
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            Select a citation badge from the chat message to inspect its ground-truth source context.
          </Typography>
        )}

        {/* Other Citations in this Answer */}
        {allCitations.length > 1 && (
          <Box sx={{ mt: 4 }}>
            <Divider sx={{ mb: 2 }} />
            <Typography
              variant="subtitle2"
              sx={{
                color: "text.secondary",
                textTransform: "uppercase",
                fontSize: "0.75rem",
                letterSpacing: "0.05em",
                mb: 1.5,
              }}
            >
              All Citations For This Answer ({allCitations.length})
            </Typography>
            <List disablePadding>
              {allCitations.map((c) => {
                const isSelected = activeCitation?.chunk_id === c.chunk_id;
                return (
                  <ListItemButton
                    key={c.chunk_id}
                    selected={isSelected}
                    onClick={() => onSelectCitation && onSelectCitation(c)}
                    sx={{
                      borderRadius: 2,
                      mb: 1,
                      border: "1px solid",
                      borderColor: isSelected ? "primary.main" : "divider",
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 32, color: isSelected ? "primary.main" : "text.secondary" }}>
                      <MenuBookIcon sx={{ fontSize: 18 }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={`[Doc ${c.doc_id}] ${c.filename}`}
                      secondary={`Page ${c.page_number}`}
                      primaryTypographyProps={{ fontSize: "0.85rem", fontWeight: isSelected ? 600 : 400, noWrap: true }}
                      secondaryTypographyProps={{ fontSize: "0.75rem" }}
                    />
                  </ListItemButton>
                );
              })}
            </List>
          </Box>
        )}
      </Box>
    </Drawer>
  );
}
