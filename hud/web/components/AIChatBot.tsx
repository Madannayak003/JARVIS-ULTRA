/* =========================================================
   JARVIS ULTRA — AI CHAT
   ========================================================= */


"use client";

import "../app/ai-chat.css";

import React, {
  KeyboardEvent,
  memo,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useVirtualizer } from "@tanstack/react-virtual";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

// * Register lightweight language grammars to keep main thread fast
import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import typescript from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import css from "react-syntax-highlighter/dist/esm/languages/prism/css";

SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("typescript", typescript);
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("jsx", jsx);
SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("bash", bash);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("css", css);

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
};

type ChatSession = {
  id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
  provider?: string;
  model?: string;
  messages?: ChatMessage[];
};

const LOCAL_DASHBOARD_URL =
  typeof window !== "undefined"
    ? `http://${window.location.hostname}:8765`
    : "http://127.0.0.1:8765";

const DASHBOARD_URL =
  process.env.NEXT_PUBLIC_JARVIS_DASHBOARD_URL || LOCAL_DASHBOARD_URL;

const DEFAULT_MODEL = "gemini-live";

type DashboardRequestErrorKind = "network" | "http" | "invalid_response";

class DashboardRequestError extends Error {
  readonly kind: DashboardRequestErrorKind;
  readonly status?: number;

  constructor(message: string, kind: DashboardRequestErrorKind, status?: number) {
    super(message);
    this.name = "DashboardRequestError";
    this.kind = kind;
    this.status = status;
  }
}

async function fetchDashboardJson<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Network request failed.";
    throw new DashboardRequestError(
      `Unable to reach the JARVIS dashboard: ${detail}`,
      "network",
    );
  }

  let data: T | { error?: string; message?: string } | null = null;
  try {
    data = await response.json();
  } catch {
    if (!response.ok) {
      throw new DashboardRequestError(
        `JARVIS dashboard returned HTTP ${response.status}.`,
        "http",
        response.status,
      );
    }
    throw new DashboardRequestError(
      "JARVIS dashboard returned an invalid response.",
      "invalid_response",
      response.status,
    );
  }

  if (!response.ok) {
    const body = data && typeof data === "object"
      ? data as { error?: string; message?: string }
      : null;
    const message = body && ("error" in body ? body.error : body.message);
    throw new DashboardRequestError(
      String(message || `JARVIS dashboard returned HTTP ${response.status}.`),
      "http",
      response.status,
    );
  }

  return data as T;
}

const wait = (milliseconds: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, milliseconds));

/* =========================================================
   MEMOIZED MESSAGE ROW (Prevents Markdown Re-parsing)
   ========================================================= */

interface MessageItemProps {
  item: ChatMessage;
  onCopy: (code: string) => void;
  copiedCode: string | null;
}

const ChatMessageItem = memo(({ item, onCopy, copiedCode }: MessageItemProps) => {
  return (
    <div className={`ai-chat-message-row ${item.role}`}>
      <div className="ai-chat-message-label">
        {item.role === "user" ? "YOU" : "AI"}
      </div>

      <div className="ai-chat-message-bubble">
        {item.role === "assistant" ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || "");
                const code = String(children).replace(/\n$/, "");

                if (!match) {
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }

                return (
                  <div className="ai-chat-code-block">
                    <div className="ai-chat-code-header">
                      <span className="ai-chat-code-language">{match[1]}</span>
                      <button
                        type="button"
                        className="ai-chat-code-copy-button"
                        onPointerDown={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          onCopy(code);
                        }}
                      >
                        {copiedCode === code ? "Copied ✓" : "Copy"}
                      </button>
                    </div>

                    <div className="ai-chat-code-scroll">
                      <SyntaxHighlighter
                        language={match[1]}
                        style={oneDark}
                        PreTag="div"
                        customStyle={{
                          margin: 0,
                          padding: "16px",
                          background: "transparent",
                          fontSize: "13px",
                          lineHeight: "1.65",
                          overflow: "visible",
                        }}
                        codeTagProps={{
                          style: {
                            fontFamily:
                              "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                          },
                        }}
                      >
                        {code}
                      </SyntaxHighlighter>
                    </div>
                  </div>
                );
              },
            }}
          >
            {item.content}
          </ReactMarkdown>
        ) : (
          item.content
        )}
      </div>
    </div>
  );
});

ChatMessageItem.displayName = "ChatMessageItem";

/* =========================================================
   MAIN COMPONENT
   ========================================================= */

export default function AIChatBot({
  open,
  onClose,
  assistantName,
}: {
  open: boolean;
  onClose?: () => void;
  assistantName: string;
}) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);
  const [modelUpdating, setModelUpdating] = useState(false);
  const [quotaError, setQuotaError] = useState<string | null>(null);

  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [renameChatId, setRenameChatId] = useState<string | null>(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [deleteChatId, setDeleteChatId] = useState<string | null>(null);
  const [chatActionLoading, setChatActionLoading] = useState(false);

  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const messagesRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const isNearBottomRef = useRef(true);

  const messages = currentSession?.messages || [];

  /* =========================================================
     VIRTUALIZATION (Smooth 60FPS with dynamic height)
     ========================================================= */

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => messagesRef.current,
    estimateSize: () => 90,
    overscan: 5,
  });

  /* =========================================================
     JITTER-FREE AUTO-SCROLL
     ========================================================= */

  const handleScroll = useCallback(() => {
    const el = messagesRef.current;
    if (!el) return;
    // * User is near bottom if within 120px threshold
    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    isNearBottomRef.current = distanceToBottom < 120;
  }, []);

  useEffect(() => {
    if (!messagesRef.current || !isNearBottomRef.current) return;

    // * Smoothly push view down only when user is actually pinned to the bottom
    requestAnimationFrame(() => {
      if (messages.length > 0) {
        virtualizer.scrollToIndex(messages.length - 1, {
          align: "end",
          behavior: "smooth",
        });
      }
    });
  }, [messages.length, loading, virtualizer]);

  /* =========================================================
     HISTORY & API
     ========================================================= */

  const loadChat = useCallback(async (sessionId: string) => {
    try {
      const data = await fetchDashboardJson<{ success?: boolean; chat?: ChatSession }>(
        `${DASHBOARD_URL}/api/ai-chat/${encodeURIComponent(sessionId)}`,
        {
          cache: "no-store",
        },
      );
      if (data?.success && data.chat) {
        setCurrentSession(data.chat);
        setHistoryError(null);
        isNearBottomRef.current = true;
        return true;
      }
      throw new DashboardRequestError(
        "The dashboard returned no chat for that session.",
        "invalid_response",
      );
    } catch (error) {
      if (error instanceof DashboardRequestError && error.status === 404) {
        setCurrentSession((previous) => (previous?.id === sessionId ? null : previous));
        setHistoryError("That conversation is no longer available.");
        console.warn("[AI CHAT] Chat session was not found:", sessionId);
      } else {
        setHistoryError(
          error instanceof DashboardRequestError
            ? error.message
            : "Unable to load that conversation.",
        );
        console.error("[AI CHAT] Failed to load chat:", error);
      }
      return false;
    }
  }, []);

  const loadChats = useCallback(async () => {
    let lastError: unknown = null;
    try {
      setLoadingHistory(true);
      setHistoryError(null);

      // The Python dashboard starts immediately after the Next.js process.
      // Retry only connectivity failures so a startup race is recoverable;
      // HTTP errors and malformed responses are surfaced immediately.
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          const data = await fetchDashboardJson<{
            success?: boolean;
            chats?: ChatSession[];
          }>(`${DASHBOARD_URL}/api/ai-chat/chats`, { cache: "no-store" });

          if (!data?.success || !Array.isArray(data.chats)) {
            throw new DashboardRequestError(
              "JARVIS dashboard returned an invalid chat history response.",
              "invalid_response",
            );
          }

          const chats = data.chats;
          setSessions(chats);

          if (chats.length > 0 && !currentSession) {
            await loadChat(chats[0].id);
          }
          return;
        } catch (error) {
          lastError = error;
          if (!(error instanceof DashboardRequestError) || error.kind !== "network" || attempt === 2) {
            throw error;
          }
          await wait(250 * (attempt + 1));
        }
      }
    } catch (error) {
      const requestError = (error || lastError) as unknown;
      setHistoryError(
        requestError instanceof DashboardRequestError
          ? requestError.message
          : "Unable to load chat history.",
      );
      console.error("[AI CHAT] Failed to load chats:", requestError);
    } finally {
      setLoadingHistory(false);
    }
  }, [currentSession, loadChat]);

  useEffect(() => {
    void loadChats();
  }, [loadChats]);

  const createNewChat = async () => {
    try {
      const response = await fetch(`${DASHBOARD_URL}/api/ai-chat/new`, {
        method: "POST",
        cache: "no-store",
      });
      const data = await response.json();

      if (!data?.success || !data.chat) {
        throw new Error(data?.error || "Unable to create new chat.");
      }

      setCurrentSession(data.chat);
      setSessions((prev) => [data.chat, ...prev.filter((c) => c.id !== data.chat.id)]);
      setMessage("");
      isNearBottomRef.current = true;
      requestAnimationFrame(() => inputRef.current?.focus());
    } catch (error) {
      console.error("[AI CHAT] New chat failed:", error);
    }
  };

  const copyCode = useCallback(async (code: string) => {
    if (!code) return;
    try {
      try {
        const response = await fetch(`${DASHBOARD_URL}/api/ai-chat/clipboard`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
          body: JSON.stringify({ text: code }),
        });
        const data = await response.json();
        if (response.ok && data?.success) {
          setCopiedCode(code);
          setTimeout(() => setCopiedCode((c) => (c === code ? null : c)), 1500);
          return;
        }
      } catch {}

      if (navigator.clipboard) {
        await navigator.clipboard.writeText(code);
        setCopiedCode(code);
        setTimeout(() => setCopiedCode((c) => (c === code ? null : c)), 1500);
      }
    } catch (error) {
      console.error("[AI CHAT] Code copy failed:", error);
    }
  }, []);

  const sendMessage = async () => {
    const text = message.trim();
    if (!text || loading) return;

    let session = currentSession;

    if (!session) {
      try {
        const res = await fetch(`${DASHBOARD_URL}/api/ai-chat/new`, {
          method: "POST",
          cache: "no-store",
        });
        const data = await res.json();
        if (!data?.success || !data.chat) throw new Error("Unable to create chat.");
        session = data.chat;
        setCurrentSession(session);
        setSessions((prev) => [session!, ...prev]);
      } catch (err) {
        console.error("[AI CHAT] Auto chat creation failed:", err);
        return;
      }
    }

    setMessage("");
    setLoading(true);
    isNearBottomRef.current = true;

    const optimisticUserMessage: ChatMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setCurrentSession((prev) =>
      prev ? { ...prev, messages: [...(prev.messages || []), optimisticUserMessage] } : prev
    );

    try {
      const response = await fetch(`${DASHBOARD_URL}/api/live/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ text }),
      });

      const data = await response.json();

      if (!response.ok || !data?.success) {
        const raw = String(data?.raw_error || data?.error || response.statusText);
        if (response.status === 503 || raw.includes("503") || raw.includes("UNAVAILABLE")) {
          setQuotaError(`Model "${selectedModel}" is experiencing high demand. Please try again later.`);
          return;
        }
        if (response.status === 429 || raw.includes("429") || raw.includes("RESOURCE_EXHAUSTED")) {
          setQuotaError(`Model "${selectedModel}" exceeded quota limit.`);
          return;
        }
        throw new Error(data?.error || `Request failed (${response.status})`);
      }

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.response || "Sent to Gemini Live. The response will appear in the live activity stream.",
        timestamp: new Date().toISOString(),
      };

      setCurrentSession((prev) =>
        prev
          ? {
              ...prev,
              messages: [...(prev.messages || []), assistantMessage],
              title: prev.title === "New Chat" ? text.slice(0, 60) : prev.title,
              updated_at: new Date().toISOString(),
            }
          : prev
      );

      await loadChats();
    } catch (error) {
      console.error("[AI CHAT] Send failed:", error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: error instanceof Error ? `Unable to respond: ${error.message}` : "Unable to respond.",
        timestamp: new Date().toISOString(),
      };

      setCurrentSession((prev) =>
        prev ? { ...prev, messages: [...(prev.messages || []), errorMessage] } : prev
      );
    } finally {
      setLoading(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  };

  const changeModel = async (model: string) => {
    if (!currentSession || modelUpdating) return;
    try {
      setModelUpdating(true);
      setQuotaError(null);
      const res = await fetch(`${DASHBOARD_URL}/api/ai-chat/${currentSession.id}/model`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ model }),
      });
      const data = await res.json();
      if (!res.ok || !data?.success) throw new Error(data?.error || "Failed to update model");

      setSelectedModel(model);
      setCurrentSession((prev) => (prev ? { ...prev, model } : prev));
      setSessions((prev) =>
        prev.map((c) => (c.id === currentSession.id ? { ...c, model } : c))
      );
    } catch (err) {
      console.error("[AI CHAT] Model change failed:", err);
    } finally {
      setModelUpdating(false);
    }
  };

  const saveRenameChat = async () => {
    const chatId = renameChatId;
    const title = renameTitle.trim();
    if (!chatId || !title || chatActionLoading) return;

    try {
      setChatActionLoading(true);
      const res = await fetch(`${DASHBOARD_URL}/api/ai-chat/${chatId}/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ title }),
      });
      const data = await res.json();
      if (!res.ok || !data?.success) throw new Error("Unable to rename");

      setSessions((prev) =>
        prev.map((c) => (c.id === chatId ? { ...c, title: data.title || title } : c))
      );
      setCurrentSession((prev) =>
        prev?.id === chatId ? { ...prev, title: data.title || title } : prev
      );
      setRenameChatId(null);
      setRenameTitle("");
    } catch (err) {
      console.error(err);
    } finally {
      setChatActionLoading(false);
    }
  };

  const deleteChat = async () => {
    const chatId = deleteChatId;
    if (!chatId || chatActionLoading) return;

    try {
      setChatActionLoading(true);
      const res = await fetch(`${DASHBOARD_URL}/api/ai-chat/${chatId}`, {
        method: "DELETE",
        cache: "no-store",
      });
      const data = await res.json();
      if (!res.ok || !data?.success) throw new Error("Delete failed");

      const remaining = sessions.filter((c) => c.id !== chatId);
      setSessions(remaining);
      setDeleteChatId(null);

      if (currentSession?.id === chatId) {
        if (remaining.length > 0) {
          await loadChat(remaining[0].id);
        } else {
          await createNewChat();
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setChatActionLoading(false);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  if (!open) return null;

  return (
    <section className="ai-chat-window">
      {/* SIDEBAR */}
      <aside className="ai-chat-sidebar">
        <div className="ai-chat-brand">
          <div className="ai-chat-brand-title">
            <span className="ai-chat-robot">▣</span>
            AI Chat
          </div>
          <div className="ai-chat-brand-subtitle">INDEPENDENT GEMINI CHAT</div>
        </div>

        <button type="button" className="ai-chat-new-button" onClick={() => void createNewChat()}>
          <span>＋</span> New Chat
        </button>

        <div className="ai-chat-sidebar-section">
          <div className="ai-chat-section-title">CHAT HISTORY</div>
          <div className="ai-chat-history">
            {loadingHistory ? (
              <div className="ai-chat-empty">Loading history...</div>
            ) : historyError ? (
              <div className="ai-chat-empty">{historyError}</div>
            ) : sessions.length === 0 ? (
              <div className="ai-chat-empty">No conversations yet.</div>
            ) : (
              sessions.map((chat) => (
                <div
                  key={chat.id}
                  className={`ai-chat-history-row ${currentSession?.id === chat.id ? "active" : ""}`}
                >
                  <button
                    type="button"
                    className="ai-chat-history-item"
                    onClick={() => {
                      setOpenMenuId(null);
                      void loadChat(chat.id);
                    }}
                  >
                    <span className="ai-chat-history-icon">▸</span>
                    <span className="ai-chat-history-text">{chat.title || "New Chat"}</span>
                  </button>

                  <button
                    type="button"
                    className="ai-chat-history-menu-button"
                    aria-label={`Options for ${chat.title || "New Chat"}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpenMenuId(openMenuId === chat.id ? null : chat.id);
                    }}
                  >
                    ⋯
                  </button>

                  {openMenuId === chat.id && (
                    <div className="ai-chat-history-menu">
                      <button
                        type="button"
                        onClick={() => {
                          setOpenMenuId(null);
                          setRenameChatId(chat.id);
                          setRenameTitle(chat.title || "New Chat");
                        }}
                      >
                        <span>✎</span> Rename
                      </button>
                      <button
                        type="button"
                        className="danger"
                        onClick={() => {
                          setOpenMenuId(null);
                          setDeleteChatId(chat.id);
                        }}
                      >
                        <span>⌫</span> Delete
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="ai-chat-sidebar-footer">
          <div className="ai-chat-independent">
            <span className="ai-chat-status-dot" />
            Independent AI
          </div>
          <div className="ai-chat-model-small">Gemini</div>
        </div>
      </aside>

      {/* RENAME DIALOG */}
      {renameChatId && (
        <div className="ai-chat-dialog-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setRenameChatId(null)}>
          <div className="ai-chat-dialog" role="dialog" aria-modal="true">
            <div className="ai-chat-dialog-title">Rename chat</div>
            <div className="ai-chat-dialog-text">Choose a name for this conversation.</div>
            <input
              className="ai-chat-dialog-input"
              value={renameTitle}
              maxLength={60}
              autoFocus
              disabled={chatActionLoading}
              onChange={(e) => setRenameTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void saveRenameChat();
                if (e.key === "Escape") setRenameChatId(null);
              }}
            />
            <div className="ai-chat-dialog-actions">
              <button type="button" className="ai-chat-dialog-cancel" onClick={() => setRenameChatId(null)} disabled={chatActionLoading}>
                Cancel
              </button>
              <button type="button" className="ai-chat-dialog-primary" onClick={() => void saveRenameChat()} disabled={chatActionLoading || !renameTitle.trim()}>
                {chatActionLoading ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DELETE DIALOG */}
      {deleteChatId && (
        <div className="ai-chat-dialog-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setDeleteChatId(null)}>
          <div className="ai-chat-dialog" role="dialog" aria-modal="true">
            <div className="ai-chat-dialog-title">Delete chat?</div>
            <div className="ai-chat-dialog-text">This conversation will be permanently removed.</div>
            <div className="ai-chat-dialog-actions">
              <button type="button" className="ai-chat-dialog-cancel" onClick={() => setDeleteChatId(null)} disabled={chatActionLoading}>
                Cancel
              </button>
              <button type="button" className="ai-chat-dialog-danger" onClick={() => void deleteChat()} disabled={chatActionLoading}>
                {chatActionLoading ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MAIN CHAT */}
      <main className="ai-chat-main">
        <header className="ai-chat-header">
          <div>
            <div className="ai-chat-header-title">AI Assistant</div>
            <div className="ai-chat-header-subtitle">Gemini Live conversation</div>
          </div>

          <div className="ai-chat-header-controls">
            <div className="ai-chat-ready" title="Gemini Live is the only runtime controller">
              Gemini Live
            </div>
            <div className="ai-chat-ready">
              <span /> Ready
            </div>
            {onClose && (
              <button type="button" className="ai-chat-close" onClick={onClose} aria-label="Close AI Chat">
                ×
              </button>
            )}
          </div>
        </header>

        {quotaError && (
          <div className="ai-chat-quota-warning">
            <div>
              <strong>MODEL QUOTA REACHED</strong>
              <span>{quotaError}</span>
            </div>
            <button type="button" onClick={() => setQuotaError(null)}>×</button>
          </div>
        )}

        {/* VIRTUALIZED MESSAGES */}
        <div
          ref={messagesRef}
          className="ai-chat-messages"
          onScroll={handleScroll}
        >
          {messages.length === 0 ? (
            <div className="ai-chat-welcome">
              <div className="ai-chat-welcome-icon">◉</div>
              <div className="ai-chat-welcome-title">Welcome to AI Assistant</div>
              <div className="ai-chat-welcome-text">Ask me anything.</div>
              <div className="ai-chat-welcome-note">This chatbot is independent from {assistantName || "the main assistant"}.</div>
              <div className="ai-chat-examples">
                {["Explain quantum computing", "Write a Python function", "Explain this concept simply"].map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => {
                      setMessage(ex);
                      requestAnimationFrame(() => inputRef.current?.focus());
                    }}
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div
              className="ai-chat-virtual-track"
              style={{
                height: `${virtualizer.getTotalSize()}px`,
                width: "100%",
                position: "relative",
              }}
            >
              {virtualizer.getVirtualItems().map((virtualRow) => {
                const item = messages[virtualRow.index];
                return (
                  <div
                    key={virtualRow.index}
                    ref={virtualizer.measureElement}
                    data-index={virtualRow.index}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    <ChatMessageItem
                      item={item}
                      onCopy={copyCode}
                      copiedCode={copiedCode}
                    />
                  </div>
                );
              })}
            </div>
          )}

          {loading && (
            <div className="ai-chat-message-row assistant">
              <div className="ai-chat-message-label">AI</div>
              <div className="ai-chat-message-bubble ai-chat-thinking">
                <span /><span /><span />
              </div>
            </div>
          )}
        </div>

        {/* COMPOSER */}
        <div className="ai-chat-composer">
          <div className="ai-chat-input-shell">
            <button type="button" className="ai-chat-input-tool" title="Settings" aria-label="Settings">
              ⚙
            </button>
            <button type="button" className="ai-chat-input-tool" title="Attach file" aria-label="Attach file">
              ⌕
            </button>

            <textarea
              ref={inputRef}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                const el = e.target;
                el.style.height = "auto";
                el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
              }}
              onKeyDown={handleKeyDown}
              placeholder="Message independent AI..."
              rows={1}
              disabled={loading}
            />

            <button
              type="button"
              className="ai-chat-send"
              onClick={() => void sendMessage()}
              disabled={!message.trim() || loading}
              aria-label="Send message"
            >
              ➤
            </button>
          </div>
          <div className="ai-chat-composer-note">
            Independent Gemini conversation · No {assistantName || "main assistant"} context
          </div>
        </div>
      </main>
    </section>
  );
}
