"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Paper,
  Chip,
  CircularProgress,
  Avatar,
  Tooltip,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import BookmarkIcon from "@mui/icons-material/Bookmark";
import ReactMarkdown from "react-markdown";
import { streamChat } from "../services/api";
import { ChatMessage, CitationSource } from "../types";

interface ChatWindowProps {
  activeNotebookId: string;
  onOpenCitation: (citation: CitationSource, allCitations: CitationSource[]) => void;
}

export default function ChatWindow({
  activeNotebookId,
  onOpenCitation,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll as stream updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (queryText?: string) => {
    const query = (queryText || inputQuery).trim();
    if (!query || !activeNotebookId || isStreaming) return;

    setInputQuery("");
    const userMsgId = `user-${Date.now()}`;
    const aiMsgId = `ai-${Date.now()}`;

    // Append user message
    const userMessage: ChatMessage = {
      id: userMsgId,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    // Append initial empty AI message
    const aiMessage: ChatMessage = {
      id: aiMsgId,
      sender: "ai",
      text: "",
      citations: [],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, aiMessage]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await streamChat(
        query,
        activeNotebookId,
        {
          onToken: (token) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiMsgId ? { ...msg, text: msg.text + token } : msg
              )
            );
          },
          onCitations: (citations) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiMsgId ? { ...msg, citations: citations } : msg
              )
            );
          },
          onError: (errMsg) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiMsgId
                  ? { ...msg, text: msg.text + `\n\n*(Error: ${errMsg})*`, isStreaming: false }
                  : msg
              )
            );
          },
        },
        controller.signal
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiMsgId
            ? { ...msg, text: msg.text + `\n\n*(Connection error: ${err.message})*`, isStreaming: false }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
      setMessages((prev) =>
        prev.map((msg) => (msg.id === aiMsgId ? { ...msg, isStreaming: false } : msg))
      );
      abortControllerRef.current = null;
    }
  };

  /**
   * Parse text to replace inline citations like [Doc 1, Page 4] with interactive chips.
   */
  const renderMessageContent = (text: string, citations: CitationSource[] = []) => {
    const citationRegex = /\[Doc\s+(\d+),\s*Page\s+(\d+)\]/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = citationRegex.exec(text)) !== null) {
      const matchIndex = match.index;
      // Push preceding text as markdown
      if (matchIndex > lastIndex) {
        parts.push(
          <ReactMarkdown key={`md-${lastIndex}`}>
            {text.substring(lastIndex, matchIndex)}
          </ReactMarkdown>
        );
      }

      const docId = parseInt(match[1], 10);
      const pageNum = parseInt(match[2], 10);
      const matchedCitation = citations.find((c) => c.doc_id === docId);

      parts.push(
        <Tooltip
          key={`cite-${matchIndex}`}
          title={matchedCitation ? `Source: ${matchedCitation.filename} (Page ${pageNum})` : "Click to view citation"}
        >
          <Chip
            size="small"
            icon={<BookmarkIcon sx={{ fontSize: 13 }} />}
            label={`Doc ${docId}, p.${pageNum}`}
            color="primary"
            variant="filled"
            onClick={() => {
              if (matchedCitation) {
                onOpenCitation(matchedCitation, citations);
              } else if (citations.length > 0) {
                onOpenCitation(citations[0], citations);
              }
            }}
            sx={{
              mx: 0.5,
              height: 22,
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
              borderRadius: "6px",
              verticalAlign: "middle",
              "&:hover": {
                backgroundColor: "primary.dark",
              },
            }}
          />
        </Tooltip>
      );

      lastIndex = matchIndex + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push(
        <ReactMarkdown key={`md-${lastIndex}`}>
          {text.substring(lastIndex)}
        </ReactMarkdown>
      );
    }

    return parts.length > 0 ? parts : <ReactMarkdown>{text}</ReactMarkdown>;
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%", width: "100%", overflow: "hidden" }}>
      {/* Messages Thread */}
      <Box sx={{ flexGrow: 1, overflowY: "auto", p: { xs: 2, md: 3 } }}>
        {messages.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 8, maxWidth: 540, mx: "auto" }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: "14px",
                background: "linear-gradient(135deg, #6366f1 0%, #38bdf8 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                mx: "auto",
                mb: 2,
              }}
            >
              <AutoAwesomeIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
              Academic Study Assistant
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
              Ask questions about your uploaded materials in <b>{activeNotebookId || "selected notebook"}</b>.
              Every answer is strictly grounded with source citations.
            </Typography>

            {/* Quick Starter Queries */}
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, justifyContent: "center" }}>
              {[
                "Summarize the main concepts in my notes",
                "Explain the key definitions and formulas",
                "What are the core mechanisms discussed?",
              ].map((starter) => (
                <Chip
                  key={starter}
                  label={starter}
                  variant="outlined"
                  onClick={() => handleSend(starter)}
                  sx={{
                    borderRadius: 2,
                    borderColor: "rgba(148, 163, 184, 0.2)",
                    "&:hover": { borderColor: "primary.main", backgroundColor: "rgba(99, 102, 241, 0.08)" },
                  }}
                />
              ))}
            </Box>
          </Box>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === "user";
            return (
              <Box
                key={msg.id}
                sx={{
                  display: "flex",
                  gap: 1.5,
                  mb: 2.5,
                  justifyContent: isUser ? "flex-end" : "flex-start",
                }}
              >
                {!isUser && (
                  <Avatar
                    sx={{
                      bgcolor: "primary.main",
                      width: 32,
                      height: 32,
                      fontSize: "0.85rem",
                    }}
                  >
                    <AutoAwesomeIcon sx={{ fontSize: 18 }} />
                  </Avatar>
                )}

                <Box sx={{ maxWidth: { xs: "85%", md: "75%" } }}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                      backgroundColor: isUser ? "#1e293b" : "background.paper",
                      border: "1px solid",
                      borderColor: isUser ? "rgba(99, 102, 241, 0.3)" : "divider",
                      lineHeight: 1.6,
                      fontSize: "0.92rem",
                    }}
                  >
                    {isUser ? (
                      <Typography variant="body2" sx={{ fontSize: "0.92rem", color: "text.primary" }}>
                        {msg.text}
                      </Typography>
                    ) : (
                      <Box sx={{ "& p": { m: 0, mb: 1, "&:last-child": { mb: 0 } } }}>
                        {renderMessageContent(msg.text, msg.citations)}
                        {msg.isStreaming && (
                          <Box
                            component="span"
                            sx={{
                              display: "inline-block",
                              width: 6,
                              height: 14,
                              backgroundColor: "primary.main",
                              ml: 0.5,
                              verticalAlign: "middle",
                              animation: "blink 1s infinite",
                              "@keyframes blink": {
                                "0%, 100%": { opacity: 1 },
                                "50%": { opacity: 0 },
                              },
                            }}
                          />
                        )}
                      </Box>
                    )}
                  </Paper>

                  {/* Timestamp & Citations Summary for AI message */}
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5, px: 0.5 }}>
                    <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.7rem" }}>
                      {msg.timestamp}
                    </Typography>
                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <Chip
                        label={`${msg.citations.length} cited ${msg.citations.length === 1 ? "source" : "sources"}`}
                        size="small"
                        variant="outlined"
                        onClick={() => onOpenCitation(msg.citations![0], msg.citations!)}
                        sx={{
                          height: 18,
                          fontSize: "0.65rem",
                          cursor: "pointer",
                          borderColor: "rgba(148, 163, 184, 0.2)",
                        }}
                      />
                    )}
                  </Box>
                </Box>

                {isUser && (
                  <Avatar
                    sx={{
                      bgcolor: "secondary.dark",
                      width: 32,
                      height: 32,
                    }}
                  >
                    <PersonOutlineIcon sx={{ fontSize: 18 }} />
                  </Avatar>
                )}
              </Box>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Bar */}
      <Box
        sx={{
          p: 2,
          borderTop: "1px solid",
          borderColor: "divider",
          backgroundColor: "background.paper",
        }}
      >
        <Box sx={{ maxWidth: 840, mx: "auto", display: "flex", alignItems: "center", gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            size="small"
            placeholder={
              activeNotebookId
                ? `Ask a question about ${activeNotebookId}...`
                : "Select a notebook to start asking questions..."
            }
            disabled={!activeNotebookId || isStreaming}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: 3,
                backgroundColor: "background.default",
              },
            }}
          />
          <IconButton
            color="primary"
            disabled={!inputQuery.trim() || !activeNotebookId || isStreaming}
            onClick={() => handleSend()}
            sx={{
              backgroundColor: "primary.main",
              color: "#ffffff",
              width: 40,
              height: 40,
              borderRadius: "10px",
              "&:hover": {
                backgroundColor: "primary.dark",
              },
              "&.Mui-disabled": {
                backgroundColor: "rgba(148, 163, 184, 0.12)",
                color: "text.secondary",
              },
            }}
          >
            {isStreaming ? <CircularProgress size={18} color="inherit" /> : <SendIcon sx={{ fontSize: 18 }} />}
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
}
