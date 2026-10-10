"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import JarvisOrb from "@/components/JarvisOrb";
import HudCockpit from "@/components/HudCockpit";
import AIChatBot from "@/components/AIChatBot";
import PhoneCallIsland, { type PhoneCallState } from "@/components/PhoneCallIsland";
import { QRCodeSVG } from "qrcode.react";

import {
  HUDBridge,
  type HUDConnectionStatus,
  type HUDBridgeEvent,
  type HUDState,
} from "@/lib/hudBridge";

function getDefaultAssistantColour() {
  if (typeof document === "undefined") {
    return "";
  }

  const root = document.documentElement;

  const inlineColour = root.style.getPropertyValue("--assistant-colour").trim();

  if (inlineColour) {
    root.style.removeProperty("--assistant-colour");
  }

  const defaultColour = getComputedStyle(root)
    .getPropertyValue("--assistant-colour")
    .trim();

  if (inlineColour) {
    root.style.setProperty("--assistant-colour", inlineColour);
  }

  return defaultColour;
}

const EMPTY_STATE: HUDState = {
  status: "idle",
  voice_mode: "online",
  ai_model: "",
  current_task: "",
  task_status: "",
  listening: false,
  speaking: false,
  thinking: false,
  executing: false,
  system: {},
  notification: "",
  error: "",
  last_event: "",
  last_update: "",
};

export type HUDActivity = {
  id: string;
  speaker: "user" | "jarvis" | "live" | "sys" | "system";
  text: string;
  timestamp: string;
  personalLinks?: PersonalLinkEntry[];
  actions?: HUDActivityAction[];
};

export type HUDActivityAction = {
  id: string;
  label: string;
  action: string;
};

export type PersonalLinkEntry = {
  name: string;
  url: string;
};

function personalLinkEntries(value: unknown): PersonalLinkEntry[] {
  if (!Array.isArray(value)) return [];

  return value.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return [];

    const { name, url } = entry as Record<string, unknown>;
    if (typeof name !== "string" || typeof url !== "string") return [];

    try {
      const parsed = new URL(url);
      if (!name.trim() || !["http:", "https:"].includes(parsed.protocol)) {
        return [];
      }
      return [{ name: name.trim(), url: url.trim() }];
    } catch {
      return [];
    }
  });
}

function phoneCallStateFromPayload(value: unknown): PhoneCallState | null {
  if (!value || typeof value !== "object") return null;

  const data = value as Record<string, unknown>;
  const state = String(data.state || "").toLowerCase();
  if (!["outgoing", "ringing", "active", "disconnected"].includes(state)) {
    return null;
  }

  return {
    state: state as PhoneCallState["state"],
    direction: String(data.direction || "") as PhoneCallState["direction"],
    caller_name: String(data.caller_name ?? data.name ?? ""),
    phone_number: String(data.phone_number ?? data.number ?? ""),
    started_at: (data.started_at as number | string | null | undefined) ?? null,
  };
}

function phoneCallStatesEqual(
  left: PhoneCallState | null,
  right: PhoneCallState | null,
): boolean {
  if (left === right) return true;
  if (!left || !right) return false;
  return (
    left.state === right.state &&
    left.direction === right.direction &&
    left.caller_name === right.caller_name &&
    left.phone_number === right.phone_number &&
    left.started_at === right.started_at
  );
}

function hudStatesEqual(left: HUDState, right: HUDState): boolean {
  return (
    left.status === right.status &&
    left.voice_mode === right.voice_mode &&
    left.ai_model === right.ai_model &&
    left.current_task === right.current_task &&
    left.task_status === right.task_status &&
    left.listening === right.listening &&
    left.speaking === right.speaking &&
    left.thinking === right.thinking &&
    left.executing === right.executing &&
    left.notification === right.notification &&
    left.error === right.error &&
    left.last_event === right.last_event &&
    left.last_update === right.last_update &&
    JSON.stringify(left.system) === JSON.stringify(right.system)
  );
}

type SettingsModal = "remote" | "android" | "customise" | "settings" | null;

type ScheduleCenterTab = "reminders" | "whatsapp" | "schedules";
type ScheduleCenterData = {
  reminders: Array<Record<string, unknown>>;
  whatsapp: Array<Record<string, unknown>>;
  schedules: Array<Record<string, unknown>>;
};

type WorkspaceProject = {
  id: string;
  name: string;
  type: string;
  location: string;
  last_modified: string;
  entry_file: string;
  preview_available: boolean;
  preview_running: boolean;
  preview_url: string;
};

type IntelligenceFile = {
  id: string;
  filename: string;
  mime_type?: string;
  type?: { category?: string; supported?: boolean };
  size: number;
  processing_status: string;
  extracted_text_available?: boolean;
  error?: string;
};

type RemoteInfo = {
  ok: boolean;
  assistant_name?: string;
  url: string;
  pairing_url: string;
  pairing_pin: string;
  pairing_active: boolean;
  pairing_remaining_seconds?: number;
  clients: number;
};

type AndroidStatus = {
  ok: boolean;
  adb_available: boolean;
  connected: boolean;
  device: string;
  serial: string;
  model: string;
  connection_type: "USB" | "Wireless" | "";
  endpoint: string;
  wireless_endpoints: string[];
  android_version: string;
  error?: string;
};

const EMPTY_ANDROID_STATUS: AndroidStatus = {
  ok: true,
  adb_available: false,
  connected: false,
  device: "",
  serial: "",
  model: "",
  connection_type: "",
  endpoint: "",
  wireless_endpoints: [],
  android_version: "",
};

const LOCAL_DASHBOARD_URL =
  typeof window !== "undefined"
    ? `http://${window.location.hostname}:8765`
    : "http://127.0.0.1:8765";

const JARVIS_DASHBOARD_URL =
  process.env.NEXT_PUBLIC_JARVIS_OFFLINE === "1"
    ? LOCAL_DASHBOARD_URL
    : process.env.NEXT_PUBLIC_JARVIS_DASHBOARD_URL || LOCAL_DASHBOARD_URL;

const HUD_BRIDGE_URL =
  process.env.NEXT_PUBLIC_JARVIS_OFFLINE === "1"
    ? (typeof window !== "undefined"
        ? `http://${window.location.hostname}:8766`
        : "http://127.0.0.1:8766")
    : process.env.NEXT_PUBLIC_JARVIS_HUD_BRIDGE_URL ||
      (typeof window !== "undefined"
        ? `http://${window.location.hostname}:8766`
        : "http://127.0.0.1:8766");

const DEFAULT_ASSISTANT_NAME = "";

function normalizeAssistantName(value: unknown): string {
  if (typeof value !== "string") {
      return "";
  }

  const name = value.trim();
  if (!name) {
    return "";
  }

  return name;
}

function displayTime(value: unknown): string {
  if (!value) return "Time not set";
  const date = new Date(String(value));
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function formatPairingRemaining(value: unknown): string {
  const seconds = Math.max(0, Math.floor(Number(value) || 0));
  const minutes = Math.floor(seconds / 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

function ScheduleCenterSection({ tab, data }: { tab: ScheduleCenterTab; data: ScheduleCenterData }) {
  const items = data[tab];
  const next = items
    .filter((item) => item.enabled !== false && item.completed !== true && item.cancelled !== true)
    .sort((left, right) => new Date(String(left.next_run_at ?? left.remind_at ?? left.send_at ?? "")).getTime() - new Date(String(right.next_run_at ?? right.remind_at ?? right.send_at ?? "")).getTime())[0];
  const title = tab === "reminders" ? "NEXT REMINDER" : tab === "whatsapp" ? "NEXT WHATSAPP" : "NEXT SCHEDULE";
  const summary = tab === "reminders" ? String(next?.text ?? "") : tab === "whatsapp" ? `Message to ${String(next?.contact ?? "contact")}` : String(next?.command ?? "");
  const time = next?.next_run_at ?? next?.remind_at ?? next?.send_at;
  return (
    <div className={`schedule-center-content schedule-center-content--${tab}`}>
      {next && <div className="schedule-center-next"><span>{title}</span><strong>{summary}</strong><small>{displayTime(time)}</small></div>}
      {!next && <div className="schedule-center-empty">{tab === "reminders" ? "No reminders scheduled." : tab === "whatsapp" ? "No WhatsApp schedules." : "No scheduled tasks."}</div>}
      <div className="schedule-center-list">
        {items.filter((item) => item !== next).map((item, index) => {
          const label = tab === "reminders" ? String(item.text ?? "Reminder") : tab === "whatsapp" ? `${String(item.contact ?? "Contact")}: ${String(item.message ?? "")}` : String(item.command ?? "Scheduled task");
          const status = item.enabled === false || item.completed === true || item.cancelled === true ? "DISABLED" : "ACTIVE";
          if (tab === "schedules") {
            return (
              <div className="schedule-center-task-row" key={String(item.id ?? index)}>
                <div className="schedule-center-task-main">
                  <strong>{label}</strong>
                  <span className={`schedule-center-task-status schedule-center-task-status--${status.toLowerCase()}`}>{status}</span>
                </div>
                <time>{displayTime(item.next_run_at ?? item.run_at)}</time>
              </div>
            );
          }
          return <div className="schedule-center-item" key={String(item.id ?? index)}><span>{label}</span><small>{status} · {displayTime(item.next_run_at ?? item.remind_at ?? item.send_at)}</small></div>;
        })}
      </div>
    </div>
  );
}


export default function Home() {
  const [hudState, setHudState] = useState<HUDState>(EMPTY_STATE);
  const [connection, setConnection] = useState<HUDConnectionStatus>("connecting");
  const [activities, setActivities] = useState<HUDActivity[]>([]);
  const [scheduleCenterOpen, setScheduleCenterOpen] = useState(false);
  const [scheduleCenterTab, setScheduleCenterTab] = useState<ScheduleCenterTab>("reminders");
  const [scheduleCenterData, setScheduleCenterData] = useState<ScheduleCenterData>({ reminders: [], whatsapp: [], schedules: [] });
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [workspaceProjects, setWorkspaceProjects] = useState<WorkspaceProject[]>([]);
  const [workspaceRoot, setWorkspaceRoot] = useState("");
  const [workspaceQuery, setWorkspaceQuery] = useState("");
  const [workspaceFilter, setWorkspaceFilter] = useState("ALL");
  const [workspaceMessage, setWorkspaceMessage] = useState("");
  const [workspacePreviewProjectId, setWorkspacePreviewProjectId] = useState<string | null>(null);
  const [workspaceDeleteProject, setWorkspaceDeleteProject] = useState<WorkspaceProject | null>(null);
  const [workspaceDeleteLoading, setWorkspaceDeleteLoading] = useState(false);
  const [workspacePreviewRefresh, setWorkspacePreviewRefresh] = useState(0);
  const [hudNotification, setHudNotification] = useState<{ title: string; message: string; level: string } | null>(null);
  const [phoneCall, setPhoneCall] = useState<PhoneCallState | null>(null);
  const phoneCallRef = useRef<PhoneCallState | null>(null);
  const phoneCallExitTimerRef = useRef<number | null>(null);
  const phoneCallExitTokenRef = useRef(0);
  const phoneCallDismissedRef = useRef(false);
  const [waveformLevels, setWaveformLevels] =
    useState<number[]>(Array(16).fill(0));

  const [morningBriefHeadlines, setMorningBriefHeadlines] = useState<
    Array<{
      category: string;
      title: string;
      link?: string;
    }>
  >([]);

  const [morningBriefActive, setMorningBriefActive] = useState(false);
  const [morningBriefStartedSpeaking, setMorningBriefStartedSpeaking] = useState(false);

  const morningBriefActiveRef = useRef(false);
  const morningBriefStartedSpeakingRef = useRef(false);
  const pendingHudCommandsRef = useRef<string[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneStreamRef = useRef<MediaStream | null>(null);
  const waveformFrameRef = useRef<number | null>(null);
  const waveformLevelsRef = useRef<number[]>([]);

  /* =========================================================
     SETTINGS & MODAL STATE
     ========================================================= */
  const [modal, setModal] = useState<SettingsModal>(null);
  const [aiChatOpen, setAiChatOpen] = useState(false);
  const [autoStart, setAutoStart] = useState(false);
  const [morningBrief, setMorningBrief] = useState(true);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(true);

  const [assistantName, setAssistantName] = useState(DEFAULT_ASSISTANT_NAME);
  const [userName, setUserName] = useState("");
  const [assistantColour, setAssistantColour] = useState("");

  const [showActivityLog, setShowActivityLog] = useState(true);
  const [showSystemMonitor, setShowSystemMonitor] = useState(true);
  const [showQuickTools, setShowQuickTools] = useState(true);

  const [remoteInfo, setRemoteInfo] = useState<RemoteInfo | null>(null);
  const [remoteLoading, setRemoteLoading] = useState(false);
  const [remotePinLoading, setRemotePinLoading] = useState(false);
  const [remoteMessage, setRemoteMessage] = useState("");
  const [shortcutLoading, setShortcutLoading] = useState(false);
  const [androidStatus, setAndroidStatus] = useState<AndroidStatus>(EMPTY_ANDROID_STATUS);
  const [androidIp, setAndroidIp] = useState("");
  const [androidPort, setAndroidPort] = useState("5555");
  const [androidLoading, setAndroidLoading] = useState(false);
  const [androidMessage, setAndroidMessage] = useState("");

  const [commandInput, setCommandInput] = useState("");
  const [commandSending, setCommandSending] = useState(false);
  const [intelligenceFiles, setIntelligenceFiles] = useState<IntelligenceFile[]>([]);
  const [fileUploadMessage, setFileUploadMessage] = useState("");
  const [filePanel, setFilePanel] = useState<{ id: string; filename: string; text: string; label: "FILE CONTENT" | "JARVIS SUMMARY" } | null>(null);
  const [fileSpeakingId, setFileSpeakingId] = useState<string | null>(null);
  const [summaryProcessingId, setSummaryProcessingId] = useState<string | null>(null);
  const fileSpeechPollRef = useRef<number | null>(null);
  const filePickerRef = useRef<HTMLInputElement | null>(null);

  // Keep the existing HUD file-chip state synchronized with the canonical
  // File Intelligence index. This also picks up files ingested remotely,
  // whose upload event is delivered to the remote dashboard WebSocket rather
  // than this desktop HUD's SSE bridge.
  useEffect(() => {
    let cancelled = false;

    const refreshIntelligenceFiles = async () => {
      try {
        const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/files`, {
          cache: "no-store",
        });
        const result = await response.json();
        if (!response.ok || !result.ok || cancelled) return;

        const nextFiles = Array.isArray(result.files) ? result.files as IntelligenceFile[] : [];
        setIntelligenceFiles((previous) => {
          const unchanged = previous.length === nextFiles.length && previous.every((item, index) => {
            const next = nextFiles[index];
            return next
              && item.id === next.id
              && item.filename === next.filename
              && item.processing_status === next.processing_status
              && item.size === next.size;
          });
          return unchanged ? previous : nextFiles;
        });
      } catch {
        // The existing local upload path remains authoritative when the HUD
        // list endpoint is temporarily unavailable.
      }
    };

    void refreshIntelligenceFiles();
    const syncTimer = window.setInterval(refreshIntelligenceFiles, 1000);

    return () => {
      cancelled = true;
      window.clearInterval(syncTimer);
    };
  }, []);

  // * 1. Inside your component, add an input ref:
  const commandInputRef = useRef<HTMLInputElement | null>(null);

  const applyPhoneCallState = useCallback((value: unknown) => {
    const nextCall = phoneCallStateFromPayload(value);
    if (!nextCall) {
      return;
    }

    // * HUDManager retains the last structured call payload in its state.
    // * Ignore that stale DISCONNECTED snapshot after the island has exited;
    // * a new call state below starts a fresh session.
    if (nextCall.state === "disconnected" && phoneCallDismissedRef.current) {
      return;
    }

    if (phoneCallStatesEqual(phoneCallRef.current, nextCall)) {
      return;
    }

    if (nextCall.state !== "disconnected") {
      phoneCallDismissedRef.current = false;
      phoneCallExitTokenRef.current += 1;
    }

    if (phoneCallExitTimerRef.current !== null) {
      window.clearTimeout(phoneCallExitTimerRef.current);
      phoneCallExitTimerRef.current = null;
    }

    phoneCallRef.current = nextCall;
    setPhoneCall(nextCall);

    if (nextCall.state === "disconnected") {
      const exitToken = ++phoneCallExitTokenRef.current;
      phoneCallExitTimerRef.current = window.setTimeout(() => {
        if (exitToken !== phoneCallExitTokenRef.current) {
          return;
        }
        phoneCallDismissedRef.current = true;
        phoneCallRef.current = null;
        setPhoneCall(null);
        phoneCallExitTimerRef.current = null;
      }, 2600);
    }
  }, []);

  const handleHUDState = useCallback((state: HUDState) => {
    applyPhoneCallState(state.system?.phone_call);
    setHudState((previous) => (hudStatesEqual(previous, state) ? previous : state));
  }, [applyPhoneCallState]);

  const refreshAndroidStatus = async () => {
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/android`, {
        cache: "no-store",
      });
      const result = (await response.json()) as AndroidStatus;
      if (!response.ok || !result.ok) throw new Error(result.error || "Android status unavailable.");
      const nextStatus = { ...EMPTY_ANDROID_STATUS, ...result };
      setAndroidStatus(nextStatus);
      if (nextStatus.endpoint && !androidIp.trim()) {
        const separator = nextStatus.endpoint.lastIndexOf(":");
        if (separator > 0) {
          setAndroidIp(nextStatus.endpoint.slice(0, separator).replace(/^\[|\]$/g, ""));
          setAndroidPort(nextStatus.endpoint.slice(separator + 1));
        }
      }
    } catch (error) {
      setAndroidStatus((previous) => ({
        ...EMPTY_ANDROID_STATUS,
        error: error instanceof Error ? error.message : "Android status unavailable.",
      }));
    }
  };

  const openAndroidPanel = () => {
    setAndroidMessage("");
    setModal("android");
    void refreshAndroidStatus();
  };

  const refreshWorkspace = async () => {
    setWorkspaceMessage("");
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/workspace/projects`, { cache: "no-store" });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Workspace unavailable.");
      setWorkspaceRoot(String(result.workspace || ""));
      setWorkspaceProjects(Array.isArray(result.projects) ? result.projects : []);
    } catch (error) {
      setWorkspaceMessage(error instanceof Error ? error.message : "Workspace unavailable.");
    }
  };

  const openWorkspace = () => {
    setWorkspaceOpen(true);
    void refreshWorkspace();
  };

  const toggleMicrophone = async () => {
    const next = !microphoneEnabled;
    setMicrophoneEnabled(next);
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/microphone`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: next }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error);
      setMicrophoneEnabled(Boolean(result.enabled && result.connected));
    } catch (error) {
      console.error(error);
      setMicrophoneEnabled(!next);
    }
  };

  const workspaceAction = async (action: string, project: WorkspaceProject) => {
    setWorkspaceMessage("");
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/workspace/${action}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: project.id }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Workspace action failed.");
      if (action === "start-preview" || action === "stop-preview") {
        setWorkspaceProjects((items) => items.map((item) => item.id === project.id ? { ...item, ...result.project } : item));
      }
      if (action === "start-preview") setWorkspacePreviewProjectId(project.id);
      if (action === "open-folder") setWorkspaceMessage(`Opened ${project.name}.`);
      if (action === "delete") {
        setWorkspaceDeleteProject(null);
        setWorkspaceDeleteLoading(false);
        if (workspacePreviewProjectId === project.id) setWorkspacePreviewProjectId(null);
        await refreshWorkspace();
      }
    } catch (error) {
      if (action === "delete") setWorkspaceDeleteLoading(false);
      setWorkspaceMessage(error instanceof Error ? error.message : "Workspace action failed.");
    }
  };

  const requestWorkspaceDelete = (project: WorkspaceProject) => {
    setWorkspaceMessage("");
    setWorkspaceDeleteProject(project);
  };

  const confirmWorkspaceDelete = async () => {
    if (!workspaceDeleteProject || workspaceDeleteLoading) return;
    setWorkspaceDeleteLoading(true);
    await workspaceAction("delete", workspaceDeleteProject);
  };

  const connectAndroid = async () => {
    const ip = androidIp.trim();
    const port = androidPort.trim() || "5555";
    if (!ip) {
      setAndroidMessage("Enter the phone IP address.");
      return;
    }

    setAndroidLoading(true);
    setAndroidMessage("");
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/android/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ ip, port }),
      });
      const result = await response.json();
      if (result.status) setAndroidStatus({ ...EMPTY_ANDROID_STATUS, ...result.status });
      if (!response.ok || !result.ok) {
        throw new Error(result.error || "Unable to connect to Android device.");
      }
      window.localStorage.setItem("jarvis-android-endpoint", JSON.stringify({ ip, port }));
      setAndroidMessage("Android device connected.");
    } catch (error) {
      setAndroidMessage(error instanceof Error ? error.message : "Android connection failed.");
      await refreshAndroidStatus();
    } finally {
      setAndroidLoading(false);
    }
  };

  const disconnectAndroid = async () => {
    setAndroidLoading(true);
    setAndroidMessage("");
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/android/disconnect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ endpoint: androidStatus.endpoint }),
      });
      const result = await response.json();
      if (result.status) setAndroidStatus({ ...EMPTY_ANDROID_STATUS, ...result.status });
      if (!response.ok || !result.ok) {
        throw new Error(result.error || "Unable to disconnect Android device.");
      }
      setAndroidMessage("Android device disconnected.");
    } catch (error) {
      setAndroidMessage(error instanceof Error ? error.message : "Android disconnection failed.");
      await refreshAndroidStatus();
    } finally {
      setAndroidLoading(false);
    }
  };

  // ! 2. Automatically restore cursor focus whenever sending completes:
  useEffect(() => {
    if (!commandSending) {
      commandInputRef.current?.focus();
    }
  }, [commandSending]);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("jarvis-android-endpoint");
      if (saved) {
        const endpoint = JSON.parse(saved);
        if (typeof endpoint.ip === "string") setAndroidIp(endpoint.ip);
        if (typeof endpoint.port === "string" || typeof endpoint.port === "number") {
          setAndroidPort(String(endpoint.port));
        }
      }
    } catch {}

    void refreshAndroidStatus();
    const statusInterval = window.setInterval(() => {
      void refreshAndroidStatus();
    }, 5000);
    return () => window.clearInterval(statusInterval);
  }, []);

  /* =========================================================
     LOAD SETTINGS
     ========================================================= */
  useEffect(() => {
    let isMounted = true;

    try {
      const saved = window.localStorage.getItem("jarvis-pro-settings");
      if (saved) {
        const settings = JSON.parse(saved);
        if (typeof settings.autoStart === "boolean") setAutoStart(settings.autoStart);
        if (typeof settings.morningBrief === "boolean") setMorningBrief(settings.morningBrief);
        if (typeof settings.userName === "string") setUserName(settings.userName);
        if (typeof settings.assistantColour === "string") {
          setAssistantColour(settings.assistantColour);
          document.documentElement.style.setProperty("--assistant-colour", settings.assistantColour);
        }
        if (typeof settings.showActivityLog === "boolean") {
          setShowActivityLog(settings.showActivityLog);
        }

        if (typeof settings.showSystemMonitor === "boolean") {
          setShowSystemMonitor(settings.showSystemMonitor);
        }

        if (typeof settings.showQuickTools === "boolean") {
          setShowQuickTools(settings.showQuickTools);
        }
        }
      } catch (error) {
        console.error("[HUD] Local settings fallback failed:", error);
      }

    const loadWithRetry = async (fn: () => Promise<void>, retries = 5, delay = 1000) => {
      for (let i = 0; i < retries; i++) {
        if (!isMounted) return;
        try {
          await fn();
          return;
        } catch {
          await new Promise((res) => setTimeout(res, delay));
        }
      }
    };

    loadWithRetry(async () => {
      const res = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/customise`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.ok && isMounted) {
          if (data.assistantName) {
            setAssistantName(normalizeAssistantName(data.assistantName));
          }
          if (data.userName) setUserName(data.userName);
          if (data.assistantColour) {
            setAssistantColour(data.assistantColour);
            document.documentElement.style.setProperty("--assistant-colour", data.assistantColour);
          }
        }
      }
    });

    loadWithRetry(async () => {
      const res = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/autostart`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.ok && isMounted) setAutoStart(data.enabled);
      }
    });

    loadWithRetry(async () => {
      const res = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/microphone`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.ok && isMounted) setMicrophoneEnabled(Boolean(data.enabled && data.connected));
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  /* =========================================================
     MICROPHONE STATUS & SYNC
     ========================================================= */
  useEffect(() => {
    let isMounted = true;

    const syncMicrophone = async () => {
      if (!isMounted) return;
      try {
        const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/microphone`, {
          cache: "no-store",
        });
        const result = await response.json();
        if (response.ok && result.ok && typeof result.enabled === "boolean" && isMounted) {
          setMicrophoneEnabled(Boolean(result.enabled && result.connected));
        }
      } catch {}
    };

    const initialTimeout = window.setTimeout(syncMicrophone, 1500);
    const syncInterval = window.setInterval(syncMicrophone, 3000);

    return () => {
      isMounted = false;
      window.clearTimeout(initialTimeout);
      window.clearInterval(syncInterval);
    };
  }, []);

  /* =========================================================
   LIVE MICROPHONE WAVEFORM ANALYSER
   ========================================================= */
  useEffect(() => {
    let cancelled = false;

    const startWaveformAnalyser = async () => {
      try {
        if (cancelled) return;

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        microphoneStreamRef.current = stream;

        const AudioContextClass =
          window.AudioContext ||
          (window as typeof window & {
            webkitAudioContext?: typeof AudioContext;
          }).webkitAudioContext;

        if (!AudioContextClass) return;

        const audioContext = new AudioContextClass();
        const analyser = audioContext.createAnalyser();

        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.72;

        const source =
          audioContext.createMediaStreamSource(stream);

        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;

        const data = new Uint8Array(analyser.fftSize);

        const updateWaveform = () => {
          if (cancelled) return;

          const currentAnalyser = analyserRef.current;

          if (!currentAnalyser) return;

          currentAnalyser.getByteTimeDomainData(data);

          let sum = 0;

          for (let i = 0; i < data.length; i++) {
            const normalized =
              (data[i] - 128) / 128;

            sum += normalized * normalized;
          }

          const rms = Math.sqrt(sum / data.length);

          const level = Math.min(
            1,
            Math.max(0, rms * 5.5)
          );

          const levels = Array.from(
            { length: 16 },
            (_, index) => {
              const centerDistance =
                Math.abs(index - 7.5) / 7.5;

              const falloff =
                1 - centerDistance * 0.45;

              const variation =
                0.82 +
                Math.sin(
                  performance.now() * 0.012 +
                  index * 0.9
                ) * 0.18;

              return Math.min(
                1,
                level * falloff * variation
              );
            }
          );

          waveformLevelsRef.current = levels;
          setWaveformLevels(levels);

          waveformFrameRef.current =
            requestAnimationFrame(updateWaveform);
          };

        updateWaveform();
      } catch (error) {
        console.warn(
          "[HUD WAVEFORM] Microphone analyser unavailable:",
          error
        );
      }
    };

    startWaveformAnalyser();

    return () => {
      cancelled = true;

      if (waveformFrameRef.current !== null) {
        cancelAnimationFrame(
          waveformFrameRef.current
        );
        waveformFrameRef.current = null;
      }

      microphoneStreamRef.current
        ?.getTracks()
        .forEach((track) => track.stop());

      microphoneStreamRef.current = null;

      void audioContextRef.current?.close();

      audioContextRef.current = null;
      analyserRef.current = null;
    };
  }, []);

  /* =========================================================
     MORNING BRIEF STATUS SYNC
     ========================================================= */
  useEffect(() => {
    let cancelled = false;

    const loadMorningBrief = async () => {
      if (cancelled) return;
      try {
        const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/morning-brief`, {
          cache: "no-store",
        });
        const result = await response.json();
        if (response.ok && result.ok && typeof result.enabled === "boolean" && !cancelled) {
          setMorningBrief(result.enabled);
        }
      } catch {}
    };

    loadMorningBrief();
    const syncTimer = window.setInterval(loadMorningBrief, 1000);

    return () => {
      cancelled = true;
      window.clearInterval(syncTimer);
    };
  }, []);

  /* =========================================================
     HUD SSE CONNECTION (STRICT DEDUPLICATION)
     ========================================================= */
  useEffect(() => {
    let speakTimer: number | null = null;
    const consumedHudEventIds = new Set<string>();

    const stopHudSpeaking = () => {
      // * End the temporary morning-brief speaking lock.
      // * The brief overlay can remain visible, but speech itself
      // ! must no longer keep the HUD in SPEAKING state.
      setMorningBriefStartedSpeaking(false);
      morningBriefStartedSpeakingRef.current = false;

      setHudState((prev) => ({
        ...prev,
        speaking: false,
        status: prev.listening ? "listening" : "idle",
      }));
    };

    const scheduleHudSpeakingStop = (delay: number) => {
      if (speakTimer !== null) {
        window.clearTimeout(speakTimer);
      }

      speakTimer = window.setTimeout(() => {
        speakTimer = null;
        stopHudSpeaking();
      }, delay);
  };

    const bridge = new HUDBridge(
      HUD_BRIDGE_URL,
      handleHUDState,
      (event: HUDBridgeEvent) => {
        if (event.name === "system_update") {
          // * State delivery is authoritative; this fallback also supports
          // * older bridge payloads that omit the nested state snapshot.
          applyPhoneCallState(event.data?.phone_call);
          return;
        }

        if (event.name === "morning_brief") {
          const headlines = Array.isArray(event.data?.headlines) ? event.data.headlines : [];
          if (headlines.length > 0) {
            setMorningBriefHeadlines(headlines);
            setMorningBriefActive(true);
            setMorningBriefStartedSpeaking(false);
            morningBriefActiveRef.current = true;
            morningBriefStartedSpeakingRef.current = false;
          }
          return;
        }

        if (event.name === "notification" || event.name === "error") {
          const title = String(event.data?.title ?? (event.name === "error" ? "ERROR" : "JARVIS"));
          const message = String(event.data?.message ?? event.data?.error ?? "").trim();
          if (message) {
            setHudNotification({ title, message, level: String(event.data?.level ?? (event.name === "error" ? "ERROR" : "INFO")) });
            window.setTimeout(() => setHudNotification(null), 7000);
          }
          return;
        }

        if (event.name === "speaking") {
          if (morningBriefActiveRef.current) {
          setMorningBriefStartedSpeaking(true);
          morningBriefStartedSpeakingRef.current = true;

          // * Morning Brief can contain several headlines and may
          // * speak for much longer than the normal response window.
          // ! Do NOT use the normal fixed speaking timer here.
          setHudState((prev) => ({
            ...prev,
            speaking: true,
            status: "speaking",
          }));

          return;
        }

        setHudState((prev) => ({
          ...prev,
          speaking: true,
          status: "speaking",
        }));

        scheduleHudSpeakingStop(7000);

        return;
        }

        if (
          event.name !== "command" &&
          event.name !== "response" &&
          event.name !== "system_activity" &&
          event.name !== "personal_links"
        ) {
          return;
        }

        const links =
          event.name === "personal_links"
            ? personalLinkEntries(event.data?.entries)
            : [];

        const actions = event.name === "system_activity"
          && Array.isArray(event.data?.actions)
          ? event.data.actions.flatMap((action: unknown) => {
              if (!action || typeof action !== "object") return [];
              const value = action as Record<string, unknown>;
              const id = String(value.id ?? "").trim();
              const label = String(value.label ?? "").trim();
              const actionName = String(value.action ?? "").trim();
              return id && label && actionName ? [{ id, label, action: actionName }] : [];
            })
          : [];

        const speaker =
          event.name === "command"
            ? "user"
            : event.name === "response"
            ? event.data?.speaker === "live"
              ? "live"
              : "jarvis"
            : event.data?.speaker === "jarvis"
              ? "jarvis"
            : "system";

        const text = String(
          event.name === "system_activity"
            ? event.data?.message ?? ""
            : event.name === "personal_links"
              ? event.data?.message ?? event.data?.title ?? "MY WEBSITES"
            : event.data?.text ?? ""
        ).trim();

        if (!text && links.length === 0) return;

        const eventId = event.event_id;

        if (
          eventId
          && consumedHudEventIds.has(eventId)
        ) {
          return;
        }

        // * Consume pending user command marker to prevent duplicate logs
        if (speaker === "user") {
          const pendingIndex = pendingHudCommandsRef.current.indexOf(text);
          if (pendingIndex !== -1) {
            pendingHudCommandsRef.current.splice(pendingIndex, 1);
            if (eventId) {
              consumedHudEventIds.add(eventId);
            }
            return;
          }
        }

        if (eventId) {
          consumedHudEventIds.add(eventId);
        }

        if (event.name === "response" && speaker === "jarvis") {
          setHudState((prev) => ({
            ...prev,
            speaking: true,
            status: "speaking",
          }));

          // * Each new response chunk extends the speaking window.
          // * The HUD returns to idle/listening only after speech
          // * activity has stopped for the full delay.
          scheduleHudSpeakingStop(4000);
        }

        // * Strict global deduplication check
        setActivities((previous) => {
          const activity: HUDActivity = {
            id: eventId || `${event.timestamp}-${Math.random()}`,
            speaker,
            text,
            timestamp: event.timestamp,
            personalLinks: links.length > 0 ? links : undefined,
            actions: actions.length > 0 ? actions : undefined,
          };

          return [...previous, activity].slice(-30);
        });
      },
      setConnection
    );

    bridge.connect();

    return () => {
      bridge.disconnect();

      if (phoneCallExitTimerRef.current !== null) {
        window.clearTimeout(phoneCallExitTimerRef.current);
        phoneCallExitTimerRef.current = null;
      }
      phoneCallExitTokenRef.current += 1;

      if (speakTimer !== null) {
        window.clearTimeout(speakTimer);
        speakTimer = null;
      }
    };
  }, [applyPhoneCallState, handleHUDState]);

  const openScheduleCenter = async (tab: ScheduleCenterTab = scheduleCenterTab) => {
    setScheduleCenterTab(tab);
    setScheduleCenterOpen(true);
    try {
      const response = await fetch(`${HUD_BRIDGE_URL}/schedule-center`, { cache: "no-store" });
      if (!response.ok) throw new Error("Schedule Center unavailable");
      setScheduleCenterData(await response.json() as ScheduleCenterData);
    } catch (error) {
      console.error(error);
    }
  };

  /* =========================================================
     3D AVATAR STATE DISPATCHER (CONTINUOUS SPEECH LOCK)
     ========================================================= */
  useEffect(() => {
    let state: "idle" | "listening" | "thinking" | "speaking" | "executing" = "idle";

    const isSpeaking = 
      hudState.speaking || 
      morningBriefStartedSpeaking || 
      hudState.status === "speaking";

    if (isSpeaking) {
      state = "speaking";
    } else if (hudState.thinking || hudState.status === "thinking") {
      state = "thinking";
    } else if (hudState.executing) {
      state = "executing";
    } else if (hudState.listening || hudState.status === "listening") {
      state = "listening";
    }

    window.dispatchEvent(
      new CustomEvent("jarvis-assistant-state", {
        detail: { state, speaking: isSpeaking },
      })
    );
  }, [
    hudState.speaking,
    hudState.status,
    hudState.thinking,
    hudState.executing,
    hudState.listening,
    morningBriefStartedSpeaking,
  ]);

  /* =========================================================
     FULLSCREEN
     ========================================================= */
  const toggleFullscreen = async () => {
    try {
      const nativeFullscreen = (
        window as typeof window & {
          pywebview?: {
            api?: {
              toggle_fullscreen?: () => Promise<boolean>;
            };
          };
        }
      ).pywebview?.api?.toggle_fullscreen;

      if (nativeFullscreen && await nativeFullscreen()) {
        return;
      }

      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch {}
  };

  /* =========================================================
     DESKTOP SHORTCUT
     ========================================================= */
  const createDesktopShortcut = async () => {
    if (shortcutLoading) return;
    setShortcutLoading(true);

    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/shortcut`, {
        method: "POST",
        cache: "no-store",
      });
      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(data?.error || "Unable to create desktop shortcut.");
      }

      alert(data.message || `${assistantName} desktop shortcut created successfully.`);
    } catch (error) {
      console.error("[DESKTOP SHORTCUT]", error);
      alert(error instanceof Error ? error.message : "Desktop shortcut creation failed.");
    } finally {
      setShortcutLoading(false);
    }
  };

  /* =========================================================
    HUD COMMAND INPUT — INSTANT LOG UPDATE WITH RETRY
  ========================================================= */
  const sendHudCommand = async (
    directCommand?: string
  ) => {
    const text =
      (directCommand ?? commandInput).trim();

    if (!text || commandSending) {
      return;
    }

    setCommandSending(true);
    setCommandInput("");

    pendingHudCommandsRef.current.push(text);

    const userActivity: HUDActivity = {
      id: `hud-command-${Date.now()}-${Math.random()}`,
      speaker: "user",
      text,
      timestamp: new Date().toISOString(),
    };

    setActivities((previous) => [
      ...previous,
      userActivity,
    ].slice(-30));

    const dashboardEndpoint = `${JARVIS_DASHBOARD_URL}/api/command`;

    let success = false;
    let lastError = "Command could not be processed by backend.";

    const maxAttempts = process.env.NEXT_PUBLIC_JARVIS_OFFLINE === "1" ? 1 : 3;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await fetch(
          dashboardEndpoint,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            cache: "no-store",
            body: JSON.stringify({
              command: text,
              text: text,
            }),
          }
        );

        const result = await response.json();

        if (response.ok && result.ok) {
          success = true;
          break;
        }

        lastError = result?.error || result?.message || lastError;
      } catch (error) {
        lastError = error instanceof Error ? error.message : "Network error";
        await new Promise((resolve) => setTimeout(resolve, 600));
      }
    }

    if (!success) {
      console.error("[HUD COMMAND ERROR]", lastError);
      const errorActivity: HUDActivity = {
        id: `${Date.now()}-${Math.random()}`,
        speaker: "system",
        text: `COMMAND FAILED: ${lastError}`,
        timestamp: new Date().toISOString(),
      };
      setActivities((previous) => [...previous, errorActivity].slice(-30));
    }

    const pendingIndex = pendingHudCommandsRef.current.indexOf(text);
    if (pendingIndex !== -1) {
      pendingHudCommandsRef.current.splice(pendingIndex, 1);
    }

    setCommandSending(false);
  };

  const interruptCurrentActivity = async () => {
    try {
      await fetch(`${JARVIS_DASHBOARD_URL}/api/local/interrupt`, { method: "POST", cache: "no-store" });
    } catch {
      // Interrupt is best-effort and should never surface an error for an idle HUD.
    }
  };

  const uploadIntelligenceFiles = async (files: FileList | File[]) => {
    const selected = Array.from(files);
    if (!selected.length) return;
    setFileUploadMessage("");
    for (const file of selected) {
      const form = new FormData();
      form.append("file", file);
      try {
        const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/upload`, { method: "POST", body: form, cache: "no-store" });
        const result = await response.json();
        if (!response.ok || !result.ok) throw new Error(result.error || "File upload failed.");
        setIntelligenceFiles((previous) => [result.file as IntelligenceFile, ...previous.filter((item) => item.id !== result.file.id)]);
        if (result.file.processing_status === "FAILED") {
          setFileUploadMessage(`${result.file.filename}: ${result.file.error || "File processing failed."}`);
        }
      } catch (error) {
        setFileUploadMessage(error instanceof Error ? error.message : "File upload failed.");
      }
    }
  };

  const removeIntelligenceFile = async (fileId: string) => {
    if (fileSpeakingId === fileId) await stopFileSpeech();
    try {
      await fetch(`${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/${encodeURIComponent(fileId)}`, { method: "DELETE", cache: "no-store" });
    } finally {
      setIntelligenceFiles((previous) => previous.filter((item) => item.id !== fileId));
      setFilePanel((previous) => previous?.id === fileId ? null : previous);
    }
  };

  const readIntelligenceFile = async (fileId: string, summarize = false) => {
    if (summarize && summaryProcessingId) return;
    if (summarize) setSummaryProcessingId(fileId);
    try {
      const endpoint = summarize
        ? `${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/${encodeURIComponent(fileId)}/summarize`
        : `${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/${encodeURIComponent(fileId)}`;
      const response = await fetch(endpoint, { method: summarize ? "POST" : "GET", headers: summarize ? { "Content-Type": "application/json" } : undefined, body: summarize ? JSON.stringify({}) : undefined, cache: "no-store" });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "File action failed.");
      const file = intelligenceFiles.find((item) => item.id === fileId);
      setFilePanel({ id: fileId, filename: file?.filename || "File", label: summarize ? "JARVIS SUMMARY" : "FILE CONTENT", text: summarize ? String(result.text || "") : String(result.text || "No extractable text.") });
      if (!summarize) void speakIntelligenceFile(fileId);
    } catch (error) {
      setFileUploadMessage(error instanceof Error ? error.message : "File action failed.");
    } finally {
      if (summarize) setSummaryProcessingId(null);
    }
  };

  const stopFileSpeech = async () => {
    if (fileSpeechPollRef.current !== null) {
      window.clearInterval(fileSpeechPollRef.current);
      fileSpeechPollRef.current = null;
    }
    try {
      await fetch(`${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/speech/stop`, { method: "POST", cache: "no-store" });
    } catch (error) {
      setFileUploadMessage(error instanceof Error ? error.message : "Unable to speak file content.");
    } finally {
      setFileSpeakingId(null);
    }
  };

  const speakIntelligenceFile = async (fileId: string, text = "") => {
    if (fileSpeakingId) return;
    setFileSpeakingId(fileId);
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/${encodeURIComponent(fileId)}/speak`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }), cache: "no-store" });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Unable to speak file content.");
      if (result.busy) {
        setFileUploadMessage("JARVIS is already speaking.");
        setFileSpeakingId(null);
        return;
      }
      fileSpeechPollRef.current = window.setInterval(async () => {
        try {
          const statusResponse = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/speech/status`, { cache: "no-store" });
          const status = await statusResponse.json();
          if (!status.speaking) {
            await stopFileSpeech();
          }
        } catch {
          await stopFileSpeech();
        }
      }, 500);
    } catch (error) {
      setFileUploadMessage(error instanceof Error ? error.message : "Unable to speak file content.");
      setFileSpeakingId(null);
    }
  };

  const toggleFileSpeech = async () => {
    if (!filePanel) return;
    if (fileSpeakingId) {
      await stopFileSpeech();
      return;
    }
    await speakIntelligenceFile(filePanel.id, filePanel.label === "JARVIS SUMMARY" ? filePanel.text : "");
  };

  const closeFilePreview = async () => {
    if (fileSpeakingId) await stopFileSpeech();
    setFilePanel(null);
  };

  const openIntelligenceFolder = async (fileId: string) => {
    const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/file-intelligence/${encodeURIComponent(fileId)}/open-folder`, { method: "POST", cache: "no-store" });
    const result = await response.json();
    if (!response.ok || !result.ok) setFileUploadMessage(result.error || "Could not open file folder.");
  };

  /* =========================================================
     REMOTE CONTROL
     ========================================================= */
  const openRemoteControl = async () => {
    setModal("remote");
    setRemoteLoading(true);
    setRemoteMessage("");

    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/info`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Remote information unavailable");
      }

      const data = (await response.json()) as RemoteInfo;
      setRemoteInfo(data);
    } catch {
      setRemoteInfo(null);
    } finally {
      setRemoteLoading(false);
    }
  };

  useEffect(() => {
    if (modal !== "remote") return;

    const countdown = window.setInterval(() => {
      setRemoteInfo((previous) => {
        if (!previous || !previous.pairing_active) return previous;
        const remaining = Math.max(0, Math.floor(Number(previous.pairing_remaining_seconds) || 0) - 1);
        if (remaining > 0) {
          return { ...previous, pairing_remaining_seconds: remaining };
        }
        return {
          ...previous,
          pairing_active: false,
          pairing_pin: "",
          pairing_url: "",
          pairing_remaining_seconds: 0,
        };
      });
    }, 1000);

    return () => window.clearInterval(countdown);
  }, [modal]);

  const generateRemotePin = async () => {
    setRemotePinLoading(true);
    setRemoteMessage("");
    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/remote/new-pin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Unable to generate a new pairing PIN.");
      setRemoteInfo((previous) => ({
        ...(previous || { ok: true, assistant_name: assistantName, url: "", clients: 0 }),
        pairing_pin: String(result.pairing_pin || ""),
        pairing_url: String(result.pairing_url || ""),
        pairing_active: Boolean(result.pairing_active),
        pairing_remaining_seconds: Number(result.pairing_remaining_seconds || 0),
      }));
    } catch (error) {
      setRemoteMessage(error instanceof Error ? error.message : "Unable to generate a new pairing PIN.");
    } finally {
      setRemotePinLoading(false);
    }
  };

  /* =========================================================
     CUSTOMISE ASSISTANT MODAL
     ========================================================= */
  const openCustomise = () => {
    setModal("customise");
  };

  const applyAssistantSettings = async () => {
    const name = normalizeAssistantName(assistantName);
    const user = userName.trim();

    const cssDefaultColour = getDefaultAssistantColour();
    const colour = /^#[0-9a-fA-F]{6}$/.test(assistantColour)
      ? assistantColour.toLowerCase()
      : cssDefaultColour;

    setAssistantName(name);
    setUserName(user);
    setAssistantColour(colour);

    try {
      window.localStorage.setItem(
        "jarvis-pro-settings",
        JSON.stringify({
          autoStart,
          morningBrief,
          userName: user,
          assistantColour: colour,
        })
      );
    } catch (error) {
      console.error("[HUD] Local settings cache failed:", error);
    }

    try {
      const response = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/customise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({
          assistantName: name,
          userName: user,
          assistantColour: colour,
        }),
      });

      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result?.error || "Failed to save assistant settings.");
      }

      if (typeof result.settings?.assistantName === "string") {
        setAssistantName(result.settings.assistantName);
      }
      if (typeof result.settings?.userName === "string") {
        setUserName(result.settings.userName);
      }
      if (typeof result.settings?.assistantColour === "string") {
        setAssistantColour(result.settings.assistantColour);
      }

      setModal(null);
    } catch (error) {
      console.error("[HUD] Assistant settings save failed:", error);
      alert(error instanceof Error ? error.message : "Could not save assistant settings.");
    }
  };

  function AssistantColourPicker({
    value,
    onChange,
  }: {
    value: string;
    onChange: (value: string) => void;
  }) {
    const wheelRef = useRef<HTMLDivElement | null>(null);

    function hexToRgb(hex: string) {
      const clean = hex.replace("#", "");
      if (!/^[0-9a-fA-F]{6}$/.test(clean)) return null;
      return {
        r: parseInt(clean.slice(0, 2), 16),
        g: parseInt(clean.slice(2, 4), 16),
        b: parseInt(clean.slice(4, 6), 16),
      };
    }

    function rgbToHsv(r: number, g: number, b: number) {
      r /= 255; g /= 255; b /= 255;
      const max = Math.max(r, g, b), min = Math.min(r, g, b);
      const delta = max - min;
      let h = 0;
      if (delta !== 0) {
        if (max === r) h = ((g - b) / delta) % 6;
        else if (max === g) h = (b - r) / delta + 2;
        else h = (r - g) / delta + 4;
        h *= 60;
        if (h < 0) h += 360;
      }
      const s = max === 0 ? 0 : delta / max;
      return { h, s, v: max };
    }

    function hsvToHex(h: number, s: number, v: number) {
      const c = v * s;
      const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
      const m = v - c;
      let r = 0, g = 0, b = 0;
      if (h < 60) { r = c; g = x; }
      else if (h < 120) { r = x; g = c; }
      else if (h < 180) { g = c; b = x; }
      else if (h < 240) { g = x; b = c; }
      else if (h < 300) { r = x; g = c; }
      else { r = c; b = x; }

      const toHex = (n: number) =>
        Math.round(Math.max(0, Math.min(1, n + m)) * 255).toString(16).padStart(2, "0");
      return "#" + toHex(r) + toHex(g) + toHex(b);
    }

    const rgb = hexToRgb(value);
    const hsv = rgb ? rgbToHsv(rgb.r, rgb.g, rgb.b) : { h: 35, s: 1, v: 1 };
    
    // * Top-aligned angle offset (-90 deg) to match CSS conic-gradient orientation
    const angle = ((hsv.h - 90) * Math.PI) / 180;
    const radius = 38;
    const handleX = 50 + Math.cos(angle) * radius * Math.max(0.4, hsv.s);
    const handleY = 50 + Math.sin(angle) * radius * Math.max(0.4, hsv.s);

    function updateFromPointer(clientX: number, clientY: number) {
      const wheel = wheelRef.current;
      if (!wheel) return;
      const rect = wheel.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      
      const x = clientX - centerX;
      const y = clientY - centerY;
      const distance = Math.hypot(x, y);
      const maxRadius = rect.width / 2;
      
      // * Compute angle and offset by +90 deg so Red is at 12 o'clock (0 deg)
      let hue = Math.atan2(y, x) * (180 / Math.PI) + 90;
      if (hue < 0) hue += 360;
      if (hue >= 360) hue -= 360;

      const saturation = Math.min(1, Math.max(0.1, distance / maxRadius));
      onChange(hsvToHex(hue, saturation, 1));
    }

    const resetToDefault = (e: React.SyntheticEvent) => {
      e.preventDefault();
      e.stopPropagation();

      const defaultColour = getDefaultAssistantColour();

      onChange(defaultColour);
      setAssistantColour(defaultColour);

      document.documentElement.style.setProperty(
        "--assistant-colour",
        defaultColour
      );
    };

    return (
      <div className="assistant-colour-picker" style={{ position: "relative", zIndex: 10 }}>
        <div className="assistant-colour-heading" style={{ position: "relative", zIndex: 20 }}>
          <div>
            <span>UI COLOUR</span>
            <small>choose HUD accent colour</small>
          </div>
          <button
            type="button"
            className="assistant-colour-default"
            style={{
              position: "relative",
              zIndex: 30,
              cursor: "pointer",
              pointerEvents: "auto",
            }}
            onPointerDown={resetToDefault}
          >
            DEFAULT
          </button>
        </div>

        <div className="assistant-colour-wheel-area" style={{ position: "relative", zIndex: 10 }}>
          <div
            ref={wheelRef}
            className="assistant-colour-wheel"
            onPointerDown={(event) => {
              event.currentTarget.setPointerCapture(event.pointerId);
              updateFromPointer(event.clientX, event.clientY);
            }}
            onPointerMove={(event) => {
              if (event.buttons === 1) {
                updateFromPointer(event.clientX, event.clientY);
              }
            }}
            onPointerUp={(event) => {
              try {
                event.currentTarget.releasePointerCapture(event.pointerId);
              } catch {}
            }}
          >
            <div
              className="assistant-colour-wheel-handle"
              style={{ left: `${handleX}%`, top: `${handleY}%`, pointerEvents: "none" }}
            />
            <div
              className="assistant-colour-preview"
              style={{ background: value, pointerEvents: "none" }}
            />
          </div>
        </div>

        <input
          className="assistant-colour-hex"
          type="text"
          value={value}
          onChange={(event) => {
            const next = event.target.value;
            if (/^#[0-9a-fA-F]{6}$/.test(next)) {
              onChange(next.toLowerCase());
            } else {
              onChange(next);
            }
          }}
          spellCheck={false}
        />
      </div>
    );
  }

  const filteredWorkspaceProjects = workspaceProjects.filter((project) =>
    (workspaceFilter === "ALL" || (workspaceFilter === "OTHER"
      ? !["HTML", "JAVASCRIPT", "PYTHON", "ARDUINO", "ESP32"].includes(project.type.toUpperCase())
      : project.type.toUpperCase() === workspaceFilter)) &&
    project.name.toLowerCase().includes(workspaceQuery.toLowerCase())
  );
  const workspacePreviewProject = workspaceProjects.find((project) => project.id === workspacePreviewProjectId) || null;
  const workspaceHtmlCount = workspaceProjects.filter((project) => project.type.toUpperCase() === "HTML").length;
  const workspaceRunningCount = workspaceProjects.filter((project) => project.preview_running).length;

  return (
    <main
      className="jarvis-hud"
      style={
        assistantColour
          ? ({
              "--assistant-colour": assistantColour,
            } as React.CSSProperties)
          : undefined
      }
    >
      {/* =====================================================
          ULTRON ENGINE
          ===================================================== */}
      <div className="ultron-layer">
        <JarvisOrb />
      </div>

      {/* =====================================================
          CONFIGURABLE ASSISTANT COCKPIT
          ===================================================== */}
      <HudCockpit
        state={hudState}
        activities={activities}
        assistantName={assistantName}
        userName={userName}
        showActivityLog={showActivityLog}
        showSystemMonitor={showSystemMonitor}
        showQuickTools={showQuickTools}
        onSchedules={() => void openScheduleCenter()}
        onWorkspace={openWorkspace}
        morningBriefHeadlines={morningBriefHeadlines}
        onMorningBriefClose={() => {
          setMorningBriefActive(false);
          setMorningBriefHeadlines([]);
          setMorningBriefStartedSpeaking(false);
          morningBriefActiveRef.current = false;
          morningBriefStartedSpeakingRef.current = false;
        }}

        onCommand={(command) => {
          void sendHudCommand(command);
        }}

        onActivityAction={async (activityId, actionId, action) => {
          setActivities((previous) => previous.filter((item) => item.id !== activityId));
          try {
            await fetch(`${HUD_BRIDGE_URL}/action`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: actionId, action }),
            });
          } catch {
            // The permission action is one-shot; no terminal output is needed.
          }
        }}

        onFullscreen={toggleFullscreen}

        onSettings={() => {
          setModal("settings");
        }}
      />

      {phoneCall && <PhoneCallIsland call={phoneCall} />}

      {workspaceOpen && (
        <div className="workspace-center-backdrop" onClick={() => setWorkspaceOpen(false)}>
          <section className="workspace-center" onClick={(event) => event.stopPropagation()} aria-label="Workspace Project Center">
            <div className="workspace-center-header">
              <div><span className="workspace-kicker">PROJECT COMMAND CENTER</span><h2>{workspacePreviewProject ? "PROJECT PREVIEW" : "WORKSPACE"}</h2><small>{workspacePreviewProject ? workspacePreviewProject.name : (workspaceRoot || "Scanning configured workspace")}</small></div>
              <div className="workspace-center-actions">{!workspacePreviewProject && <button type="button" onClick={() => void refreshWorkspace()}>REFRESH</button>}<button type="button" onClick={() => { setWorkspacePreviewProjectId(null); setWorkspaceOpen(false); }} aria-label="Close Workspace">×</button></div>
            </div>
            {!workspacePreviewProject && <>
            <div className="workspace-summary-strip"><span><strong>{workspaceProjects.length}</strong><small>TOTAL PROJECTS</small></span><span><strong>{workspaceHtmlCount}</strong><small>HTML PROJECTS</small></span><span><strong>{workspaceProjects.length - workspaceHtmlCount}</strong><small>OTHER PROJECTS</small></span><span><strong>{workspaceRunningCount}</strong><small>ACTIVE PREVIEWS</small></span></div>
            <div className="workspace-toolbar"><input value={workspaceQuery} onChange={(event) => setWorkspaceQuery(event.target.value)} placeholder="Search projects" aria-label="Search projects" /><div>{["ALL", "HTML", "JAVASCRIPT", "PYTHON", "ARDUINO", "ESP32", "OTHER"].map((filter) => <button key={filter} type="button" className={workspaceFilter === filter ? "is-active" : ""} onClick={() => setWorkspaceFilter(filter)}>{filter}</button>)}</div></div>
            {workspaceMessage && <div className="workspace-message">{workspaceMessage}</div>}
            <div className="workspace-project-grid">
              {filteredWorkspaceProjects.map((project) => (
                <article className="workspace-project-card" key={project.id}>
                  <div className="workspace-project-top"><span className={`workspace-project-type workspace-type-${project.type.toLowerCase()}`}>{project.type}</span>{project.preview_running ? <span className="workspace-running">● RUNNING</span> : project.preview_available && <span className="workspace-available">● PREVIEW AVAILABLE</span>}</div>
                  <h3>{project.name}</h3>
                  <div className="workspace-project-meta"><span>LOCATION</span><code title={project.location}>{project.location}</code></div>
                  <div className="workspace-project-meta"><span>MODIFIED</span><code>{project.last_modified ? new Date(project.last_modified).toLocaleString() : "--"}</code></div>
                  {project.entry_file && <div className="workspace-project-entry">ENTRY · {project.entry_file}</div>}
                  {project.preview_running && <div className="workspace-preview-url">{project.preview_url}</div>}
                  <div className="workspace-project-buttons">{project.preview_available && <button type="button" onClick={() => void workspaceAction(project.preview_running ? "stop-preview" : "start-preview", project)}>{project.preview_running ? "STOP PREVIEW" : "PREVIEW"}</button>}<button type="button" onClick={() => void navigator.clipboard?.writeText(project.location).then(() => setWorkspaceMessage("Project path copied."))}>COPY PATH</button><button type="button" onClick={() => void workspaceAction("open-folder", project)}>OPEN FOLDER</button><button type="button" className="workspace-delete-button" onClick={() => requestWorkspaceDelete(project)}>DELETE</button><button type="button" className="workspace-vscode-button" onClick={() => void workspaceAction("open-vscode", project)}>OPEN IN VS CODE</button></div>
                </article>
              ))}
              {!filteredWorkspaceProjects.length && <div className="workspace-empty"><strong>NO PROJECTS DETECTED</strong><span>{workspaceMessage || "Workspace contains no matching recognized projects."}</span></div>}
            </div>
            </>}
            {workspacePreviewProject && <div className="workspace-preview-mode">
              <div className="workspace-preview-toolbar"><button type="button" onClick={() => setWorkspacePreviewProjectId(null)}>← BACK TO PROJECTS</button><button type="button" onClick={() => setWorkspacePreviewRefresh((value) => value + 1)}>↻ REFRESH PREVIEW</button><button type="button" onClick={() => void workspaceAction("open-external", workspacePreviewProject)}>OPEN EXTERNALLY</button><button type="button" onClick={() => void workspaceAction("stop-preview", workspacePreviewProject)}>STOP PREVIEW</button></div>
              <div className="workspace-preview-status"><span>● LOCAL PREVIEW</span><code>{workspacePreviewProject.preview_url}</code></div>
              {workspacePreviewProject.preview_url ? (
                <iframe key={`${workspacePreviewProject.id}-${workspacePreviewRefresh}`} className="workspace-preview-frame" src={workspacePreviewProject.preview_url} title={`${workspacePreviewProject.name} HTML preview`} sandbox="allow-forms allow-modals allow-popups allow-presentation allow-scripts allow-same-origin" />
              ) : (
                <div className="workspace-preview-initializing">INITIALIZING LOCAL PREVIEW…</div>
              )}
            </div>}
          </section>
        </div>
      )}

      {workspaceDeleteProject && (
        <div className="workspace-delete-backdrop" role="dialog" aria-modal="true" aria-label="Delete Project Confirmation">
          <section className="workspace-delete-dialog">
            <span className="workspace-delete-kicker">PROJECT DELETION</span>
            <h2>Delete Project?</h2>
            <p>Are you sure you want to delete</p>
            <strong>{workspaceDeleteProject.name}</strong>
            <small>This will permanently remove the project and its files.</small>
            <div className="workspace-delete-actions">
              <button type="button" className="workspace-delete-confirm" onClick={() => void confirmWorkspaceDelete()} disabled={workspaceDeleteLoading}>
                {workspaceDeleteLoading ? "DELETING…" : "DELETE PROJECT"}
              </button>
              <button type="button" onClick={() => setWorkspaceDeleteProject(null)} disabled={workspaceDeleteLoading}>CANCEL</button>
            </div>
          </section>
        </div>
      )}

      <AIChatBot
        open={aiChatOpen}
        onClose={() => setAiChatOpen(false)}
        assistantName={assistantName}
      />

      {/* =====================================================
          COMMAND INPUT
          ===================================================== */}
      {!workspaceOpen && (
        <div className="hud-command-dock">
          {/* INTERRUPT BUTTON (Placed first so it sits on the left) */}
          <button
            type="button"
            className="hud-interrupt-button"
            onClick={() => void interruptCurrentActivity()}
            title="Interrupt current task"
            aria-label="Interrupt current task"
          >
            <svg
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="currentColor"
              aria-hidden="true"
            >
              <rect x="5" y="5" width="14" height="14" rx="2" />
            </svg>
            <span>INTERRUPT</span>
          </button>

          <div className="hud-command-input">
            <div className="hud-command-label">◆ COMMAND INPUT</div>
            {intelligenceFiles.length > 0 && (
              <div className="hud-file-context" aria-label="Uploaded files">
                {intelligenceFiles.map((file) => (
                  <div className="hud-file-chip" key={file.id}>
                    <span title={file.filename}>{file.filename}</span>
                    <small>{file.processing_status}</small>
                    {file.processing_status === "READY" && (
                      <div className="hud-file-chip-actions">
                        <button
                          type="button"
                          onClick={() => void readIntelligenceFile(file.id)}
                          aria-label={`Read ${file.filename}`}
                        >
                          READ
                        </button>
                        <button
                          type="button"
                          onClick={() => void readIntelligenceFile(file.id, true)}
                          disabled={Boolean(summaryProcessingId)}
                          aria-label={`Summarize ${file.filename}`}
                        >
                          {summaryProcessingId === file.id
                            ? "⟳ SUMMARIZING..."
                            : "SUMMARY"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void openIntelligenceFolder(file.id)}
                          aria-label={`Open folder for ${file.filename}`}
                        >
                          FOLDER
                        </button>
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => void removeIntelligenceFile(file.id)}
                      aria-label={`Remove ${file.filename}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
            {fileUploadMessage && (
              <div className="hud-file-upload-message">{fileUploadMessage}</div>
            )}
            {filePanel && (
              <div className="hud-file-panel">
                <div>
                  <strong>{filePanel.filename}</strong>
                  <span>
                    <em>{filePanel.label}</em>
                    <button
                      type="button"
                      className="hud-file-speak-button"
                      onClick={() => void toggleFileSpeech()}
                      aria-label={
                        fileSpeakingId
                          ? "Stop file speech"
                          : "Speak file content"
                      }
                      title={
                        fileSpeakingId
                          ? "Stop file speech"
                          : "Speak file content"
                      }
                    >
                      {fileSpeakingId ? "🔊" : "🔈"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void closeFilePreview()}
                      aria-label="Close file preview"
                    >
                      ×
                    </button>
                  </span>
                </div>
                <pre>{filePanel.text}</pre>
              </div>
            )}
            <div
              className="hud-command-row"
              onClick={() => commandInputRef.current?.focus()}
            >
              <input
                ref={filePickerRef}
                className="hud-file-picker"
                type="file"
                multiple
                accept=".pdf,.txt,.md,.docx,.py,.js,.ts,.jsx,.tsx,.html,.css,.json,.xml,.yaml,.yml,.sql,.c,.cpp,.h,.java,.kt,.cs,.php,.go,.rs,.sh,.bat,.ps1,.csv,.xlsx,.png,.jpg,.jpeg,.webp"
                onChange={(event) => {
                  if (event.target.files)
                    void uploadIntelligenceFiles(event.target.files);
                  event.currentTarget.value = "";
                }}
              />

              <button
                type="button"
                className="hud-file-button"
                onClick={(event) => {
                  event.stopPropagation();
                  filePickerRef.current?.click();
                }}
                aria-label="Attach files"
                title="Attach files"
              >
                <svg
                  viewBox="0 0 24 24"
                  width="17"
                  height="17"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>

              <input
                ref={commandInputRef}
                type="text"
                value={commandInput}
                onChange={(event) => setCommandInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    void sendHudCommand();
                  }
                }}
                placeholder="Type a command or question..."
                autoComplete="off"
                autoCorrect="off"
                spellCheck={false}
                disabled={commandSending}
              />

              {/* SEND BUTTON */}
              <button
                type="button"
                onClick={() => void sendHudCommand()}
                disabled={commandSending || !commandInput.trim()}
                aria-label="Send command"
              >
                <svg
                  viewBox="0 0 24 24"
                  width="16"
                  height="16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M21.5 3.5L10.7 14.3" />
                  <path d="M21.5 3.5L14.6 21L10.7 14.3L3.5 10.4L21.5 3.5Z" />
                </svg>
              </button>

              {/* MIC BUTTON */}
              <button
                type="button"
                className={`hud-mic-button ${microphoneEnabled ? "is-active" : ""}`}
                onClick={() => void toggleMicrophone()}
                aria-label={
                  microphoneEnabled
                    ? "Disable microphone"
                    : "Enable microphone"
                }
                title={
                  microphoneEnabled
                    ? "Disable microphone"
                    : "Enable microphone"
                }
              >
                <svg
                  viewBox="0 0 24 24"
                  width="17"
                  height="17"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  {microphoneEnabled ? (
                    <>
                      <rect x="8" y="3" width="8" height="12" rx="4" />
                      <path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6" />
                    </>
                  ) : (
                    <>
                      <rect x="8" y="3" width="8" height="12" rx="4" />
                      <path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6M4 4l16 16" />
                    </>
                  )}
                </svg>
              </button>

            </div>
          </div>
        </div>
      )}

      {/* =====================================================
          MORNING BRIEF OVERLAY
          ===================================================== */}
      {morningBriefActive && morningBriefHeadlines.length > 0 && (
        <div className="morning-brief-overlay">
          <button
            type="button"
            className="morning-brief-close"
            onClick={() => {
              setMorningBriefActive(false);
              setMorningBriefHeadlines([]);
            }}
            aria-label="Close morning brief"
          >
            ×
          </button>
          <div className="morning-brief-header">
            <span className="morning-brief-marker">◆</span>
            <span>TODAY'S TOP HEADLINES</span>
          </div>
          <div className="morning-brief-list">
            {morningBriefHeadlines.map((headline, index) => (
              <div
                key={`${headline.title}-${index}`}
                className="morning-brief-item"
              >
                <span className="morning-brief-category">
                  {headline.category.toUpperCase()}
                </span>
                <span className="morning-brief-title">
                  {headline.title}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =====================================================
          CONNECTION
          ===================================================== */}
        {hudNotification && (
          <div className={`hud-notification hud-notification--${hudNotification.level.toLowerCase()}`} role="status">
            <div className="hud-notification-title">{hudNotification.title}</div>
            <div className="hud-notification-message">{hudNotification.message}</div>
          </div>
        )}

        {scheduleCenterOpen && (
          <div className="schedule-center-backdrop" role="dialog" aria-modal="true" aria-label="Schedule Center">
            <section className="schedule-center-panel">
              <button type="button" className="schedule-center-close" onClick={() => setScheduleCenterOpen(false)} aria-label="Close Schedule Center">×</button>
              <div className="schedule-center-heading">SCHEDULE CENTER</div>
              <div className="schedule-center-tabs" role="tablist">
                {(["reminders", "whatsapp", "schedules"] as ScheduleCenterTab[]).map((tab) => (
                  <button key={tab} type="button" role="tab" aria-selected={scheduleCenterTab === tab} className={scheduleCenterTab === tab ? "is-active" : ""} onClick={() => void openScheduleCenter(tab)}>
                    {tab === "reminders" ? "🔔 Reminders" : tab === "whatsapp" ? "💬 WhatsApp" : "📅 Scheduled Tasks"}
                  </button>
                ))}
              </div>
              <ScheduleCenterSection tab={scheduleCenterTab} data={scheduleCenterData} />
            </section>
          </div>
        )}

        <div className="hud-bridge-status">
        <span
          className={`hud-bridge-dot ${connection}`}
          aria-hidden="true"
        />
        <span>
          {assistantName} LINK ·{" "}
          {connection === "connected"
            ? hudState.status.toUpperCase()
            : connection.toUpperCase()}
        </span>
      </div>

      {/* =====================================================
          BOTTOM HUD: INDICATORS + WAVEFORM + 8 INLINE BUTTONS
          ===================================================== */}
      {!workspaceOpen && <div className="cockpit-bottom-container">

        {/* =====================================================
            SIRI FLUID WAVE REACTOR
            ===================================================== */}
        <div
          className={`siri-container ${
            hudState.listening &&
            !hudState.speaking &&
            hudState.status !== "speaking"
              ? "is-listening"
              : ""
          }`}
          aria-hidden="true"
        >
          <div className="siri-stage">
            {/* Horizon line */}
            <div className="siri-line" />

            {/* Siri Multi-wave SVG */}
            <svg
              className="siri-svg"
              viewBox="0 0 1000 120"
              preserveAspectRatio="none"
              fill="none"
              xmlns="http:  // * www.w3.org/2000/svg"
            >
              <defs>
                {/* Gradients matching image exact colors */}
                <linearGradient id="greenWave" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#00e676" stopOpacity="0" />
                  <stop offset="50%" stopColor="#00e676" stopOpacity="0.95" />
                  <stop offset="100%" stopColor="#00b0ff" stopOpacity="0.8" />
                </linearGradient>

                <linearGradient id="cyanWave" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.1" />
                  <stop offset="50%" stopColor="#00e5ff" stopOpacity="0.9" />
                  <stop offset="100%" stopColor="#2979ff" stopOpacity="0.8" />
                </linearGradient>

                <linearGradient id="purpleWave" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#2979ff" stopOpacity="0.8" />
                  <stop offset="70%" stopColor="#7c4dff" stopOpacity="0.85" />
                  <stop offset="100%" stopColor="#e040fb" stopOpacity="0" />
                </linearGradient>

                <linearGradient id="coreGlow" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#ffffff" stopOpacity="0" />
                  <stop offset="50%" stopColor="#ffffff" stopOpacity="1" />
                  <stop offset="100%" stopColor="#00e5ff" stopOpacity="0" />
                </linearGradient>

                <filter id="softGlow" x="-20%" y="-50%" width="140%" height="200%">
                  <feGaussianBlur stdDeviation="3.5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              {/* Layer 1: Left Green Lobe */}
              <path
                className="siri-path siri-path--green"
                filter="url(#softGlow)"
                fill="url(#greenWave)"
                d="M 280,60 Q 360,25 420,60 Q 360,95 280,60 Z"
              />

              {/* Layer 2: Deep Blue Under-Lobe */}
              <path
                className="siri-path siri-path--blue"
                filter="url(#softGlow)"
                fill="#1565c0"
                opacity="0.7"
                d="M 430,60 Q 550,15 620,60 Q 550,105 430,60 Z"
              />

              {/* Layer 3: Center-Right Cyan Lobe */}
              <path
                className="siri-path siri-path--cyan"
                filter="url(#softGlow)"
                fill="url(#cyanWave)"
                d="M 440,60 Q 535,28 610,60 Q 535,92 440,60 Z"
              />

              {/* Layer 4: Right Purple/Magenta Tail */}
              <path
                className="siri-path siri-path--purple"
                filter="url(#softGlow)"
                fill="url(#purpleWave)"
                d="M 540,60 Q 610,38 680,60 Q 610,82 540,60 Z"
              />

              {/* Layer 5: Bright Center Core Glow */}
              <path
                className="siri-path siri-path--core"
                filter="url(#softGlow)"
                fill="url(#coreGlow)"
                d="M 470,60 Q 535,46 590,60 Q 535,74 470,60 Z"
              />
            </svg>
          </div>
        </div>
        
        {/* RUNTIME INDICATORS WITH BRACKETS & GLOW DOTS */}
        <div className="cockpit-bottom-indicators">
          <div
            className={`voice-indicator ${
              hudState.listening &&
              !hudState.speaking &&
              hudState.status !== "speaking" &&
              !morningBriefStartedSpeaking
                ? "active"
                : ""
            }`}
          >
            <span className="indicator-dot" />
            <span className="indicator-label">[ LISTENING ]</span>
          </div>
          <div className={`voice-indicator ${hudState.thinking ? "active" : ""}`}>
            <span className="indicator-dot" />
            <span className="indicator-label">[ THINKING ]</span>
          </div>
          <div
            className={`voice-indicator ${
              hudState.speaking ||
              hudState.status === "speaking" ||
              morningBriefStartedSpeaking
                ? "active"
                : ""
            }`}
          >
            <span className="indicator-dot" />
            <span className="indicator-label">[ SPEAKING ]</span>
          </div>
          <div className={`voice-indicator ${hudState.executing ? "active" : ""}`}>
            <span className="indicator-dot" />
            <span className="indicator-label">[ EXECUTING ]</span>
          </div>
        </div>

      </div>}

      {/* =====================================================
          ANDROID CONNECTION MODAL
          ===================================================== */}
      {modal === "android" && (
        <div
          className="settings-modal-backdrop"
          onClick={() => setModal(null)}
        >
          <section
            className="settings-modal android-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="settings-modal-heading">
              <span className="settings-heading-icon">◆</span>
              <span>ANDROID DEVICE</span>
              <button
                type="button"
                className="settings-modal-close"
                aria-label="Close Android connection panel"
                onClick={() => setModal(null)}
              >
                ×
              </button>
            </div>

            <div className="android-modal-content">
              <div className="android-status-grid">
                <span>Status</span>
                <strong className={androidStatus.connected ? "android-connected-text" : ""}>
                  {androidStatus.connected ? "Connected" : "Disconnected"}
                </strong>
                <span>Device</span>
                <strong>{androidStatus.model || androidStatus.device || "—"}</strong>
                <span>Connection</span>
                <strong>{androidStatus.connection_type || "—"}</strong>
                {androidStatus.endpoint && (
                  <>
                    <span>Endpoint</span>
                    <strong>{androidStatus.endpoint}</strong>
                  </>
                )}
              </div>

              <div className="android-endpoint-fields">
                <label>
                  <span>IP ADDRESS</span>
                  <input
                    type="text"
                    value={androidIp}
                    onChange={(event) => setAndroidIp(event.target.value)}
                    placeholder="192.168.1.100"
                    spellCheck={false}
                  />
                </label>
                <label>
                  <span>PORT</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={androidPort}
                    onChange={(event) => setAndroidPort(event.target.value)}
                    placeholder="5555"
                    spellCheck={false}
                  />
                </label>
              </div>

              {androidMessage && <div className="android-modal-message">{androidMessage}</div>}
              {androidStatus.error && !androidMessage && (
                <div className="android-modal-message">{androidStatus.error}</div>
              )}

              <div className="settings-modal-actions">
                {(!androidStatus.connected ||
                  androidStatus.connection_type !== "Wireless" ||
                  `${androidIp.trim()}:${androidPort.trim() || "5555"}` !== androidStatus.endpoint) && (
                  <button
                    type="button"
                    className="settings-modal-button settings-modal-button-primary"
                    onClick={() => void connectAndroid()}
                    disabled={androidLoading || !androidIp.trim()}
                  >
                    {androidLoading ? "CONNECTING..." : "CONNECT"}
                  </button>
                )}
                {androidStatus.connected && androidStatus.connection_type === "Wireless" && (
                  <button
                    type="button"
                    className="settings-modal-button settings-modal-button-primary"
                    onClick={() => void disconnectAndroid()}
                    disabled={androidLoading}
                  >
                    {androidLoading ? "DISCONNECTING..." : "DISCONNECT"}
                  </button>
                )}
                <button
                  type="button"
                  className="settings-modal-button"
                  onClick={() => setModal(null)}
                >
                  DISMISS
                </button>
              </div>
            </div>
          </section>
        </div>
      )}

      {/* =====================================================
          REMOTE CONTROL MODAL
          ===================================================== */}
      {modal === "remote" && (
        <div
          className="settings-modal-backdrop"
          onClick={() => setModal(null)}
        >
          <section
            className="settings-modal remote-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="settings-modal-heading">
              <span>◆</span>
              REMOTE ACCESS
            </div>

            <div className="remote-modal-content">
              <div className="remote-title">{assistantName} REMOTE</div>
              <p className="remote-description">Scan to connect your device</p>

              {remoteLoading ? (
                <div className="remote-loading">CONNECTING TO {assistantName}...</div>
              ) : (
                <>
                  {remoteInfo?.pairing_active && remoteInfo.pairing_url ? (
                    <div className="remote-qr-wrapper">
                      <div className="remote-qr">
                        <QRCodeSVG
                          value={remoteInfo.pairing_url}
                          size={220}
                          bgColor="#050505"
                          fgColor="#ffcc66"
                          level="M"
                          includeMargin
                        />
                      </div>
                      <div className="remote-qr-label">SCAN TO CONNECT</div>
                    </div>
                  ) : (
                    <div className="remote-offline">
                      <strong>PIN EXPIRED</strong>
                      <span>Generate a new PIN to pair a device.</span>
                    </div>
                  )}

                  {remoteInfo && <>
                    <div className="remote-pin-box">
                      <span className="remote-pin-label">PAIRING PIN</span>
                      <strong className="remote-pin">{remoteInfo.pairing_active ? remoteInfo.pairing_pin : "EXPIRED"}</strong>
                      <div className="remote-pin-meta">
                        <span className={remoteInfo.pairing_active ? "remote-pin-active" : "remote-pin-expired"}>● {remoteInfo.pairing_active ? "ACTIVE" : "EXPIRED"}</span>
                        <span>EXPIRES IN {remoteInfo.pairing_active ? formatPairingRemaining(remoteInfo.pairing_remaining_seconds) : "00:00"}</span>
                      </div>
                    </div>

                    <button type="button" className="remote-new-pin-button" onClick={() => void generateRemotePin()} disabled={remotePinLoading}>
                      {remotePinLoading ? "GENERATING..." : "NEW PIN"}
                    </button>

                    <div className="remote-status-box">
                      <span>{assistantName} DASHBOARD</span>
                      <strong>{remoteInfo.url}</strong>
                    </div>

                    <div className={`remote-device-status ${remoteInfo.clients > 0 ? "is-connected" : ""}`}>
                      <span>●</span>
                      {remoteInfo.clients > 0 ? "DEVICE CONNECTED · REMOTE DEVICE AUTHENTICATED" : "WAITING FOR DEVICE"}
                    </div>
                  </>}
                  {remoteMessage && <div className="remote-message">{remoteMessage}</div>}
                </>
              )}

              <p className="remote-note">
                Scan the QR code with your phone. Your device will open the {assistantName} remote pairing page.
              </p>

              <div className="settings-modal-actions">
                <button
                  type="button"
                  className="settings-modal-button settings-modal-button-primary"
                  onClick={() => {
                    const url = remoteInfo?.pairing_url || remoteInfo?.url;
                    if (!url) return;
                    window.open(url, "_blank", "noopener,noreferrer");
                  }}
                  disabled={!remoteInfo}
                >
                  OPEN REMOTE
                </button>
                <button
                  type="button"
                  className="settings-modal-button"
                  onClick={() => setModal(null)}
                >
                  DISMISS
                </button>
              </div>
            </div>
          </section>
        </div>
      )}

      {/*===================================================
        SETTINGS MODAL
      =====================================================*/}
      {modal === "settings" && (
        <div
          className="settings-modal-backdrop"
          onClick={() => setModal(null)}
        >
          <section
            className="settings-modal settings-preferences-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="settings-modal-heading">
              <span className="settings-heading-icon">◆</span>
              <span>SETTINGS</span>

              <button
                type="button"
                className="settings-modal-close"
                aria-label="Close settings"
                onClick={() => setModal(null)}
              >
                ×
              </button>
            </div>

            <div className="settings-form">

              {/* BOTTOM ACTIONS */}
              <div className="settings-bottom-actions-section">
                <div className="settings-control-header">
                  <span className="settings-control-icon">▤</span>
                  <div>
                    <div className="settings-control-title">BOTTOM ACTIONS</div>
                    <div className="settings-control-description">
                      HUD actions and controls
                    </div>
                  </div>
                </div>
                <div className="settings-bottom-actions-grid">
                  <button
                    type="button"
                    className={`hud-bar-btn ${microphoneEnabled ? "is-active" : ""}`}
                    onClick={() => void toggleMicrophone()}
                  >
                    <span className="btn-icon"></span>
                    <span>MIC {microphoneEnabled ? "ON" : "OFF"}</span>
                  </button>
                  <button
                    type="button"
                    className={`hud-bar-btn android-status-button ${androidStatus.connected ? "is-android-connected" : ""}`}
                    onClick={openAndroidPanel}
                    aria-label="Android device connection"
                  >
                    <span className="android-status-indicator" aria-hidden="true">
                      {androidStatus.connected ? "●" : "○"}
                    </span>
                    <span>ANDROID</span>
                  </button>
                  <button type="button" className="hud-bar-btn" onClick={openRemoteControl}>
                    <span className="btn-icon"></span>
                    <span>REMOTE</span>
                  </button>
                  <button type="button" className="hud-bar-btn" onClick={() => setAiChatOpen(true)}>
                    <span>AI CHAT</span>
                  </button>
                  <button
                    type="button"
                    className={`hud-bar-btn ${morningBrief ? "is-active" : ""}`}
                    onClick={async () => {
                      const next = !morningBrief;
                      setMorningBrief(next);
                      try {
                        const res = await fetch(`${JARVIS_DASHBOARD_URL}/api/local/morning-brief`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ enabled: next }),
                        });
                        const result = await res.json();
                        if (!res.ok || !result.ok) throw new Error(result.error);
                      } catch (err) {
                        console.error(err);
                        setMorningBrief(!next);
                      }
                    }}
                  >
                    <span className="btn-icon">☀</span>
                    <span>BRIEF {morningBrief ? "ON" : "OFF"}</span>
                  </button>
                  <button
                    type="button"
                    className={`hud-bar-btn ${autoStart ? "is-active" : ""}`}
                    onClick={() => {
                      const next = !autoStart;
                      setAutoStart(next);
                      try {
                        window.localStorage.setItem(
                          "jarvis-pro-settings",
                          JSON.stringify({ autoStart: next, morningBrief, userName, assistantColour })
                        );
                      } catch {}
                    }}
                  >
                    <span className="btn-icon"></span>
                    <span>AUTO-START {autoStart ? "ON" : "OFF"}</span>
                  </button>
                  <button type="button" className="hud-bar-btn" onClick={createDesktopShortcut} disabled={shortcutLoading}>
                    <span className="btn-icon"></span>
                    <span>{shortcutLoading ? "SHORTCUT..." : "SHORTCUT"}</span>
                  </button>
                  <button type="button" className="hud-bar-btn" onClick={openCustomise}>
                    <span className="btn-icon"></span>
                    <span>CUSTOMISE</span>
                  </button>
                  <button type="button" className="hud-bar-btn" onClick={toggleFullscreen}>
                    <span className="btn-icon">⛶</span>
                    <span>FULLSCREEN</span>
                  </button>
                </div>
              </div>

              {/* HUD VISIBILITY */}
              <div className="settings-visibility-section">

                <div className="settings-control-header">
                  <span className="settings-control-icon">◉</span>

                  <div>
                    <div className="settings-control-title">
                      HUD VISIBILITY
                    </div>

                    <div className="settings-control-description">
                      Show or hide HUD panels in the cockpit
                    </div>
                  </div>
                </div>

                {/* ACTIVITY LOG */}
                <label className="settings-toggle-row">
                  <span className="settings-toggle-icon">☷</span>

                  <span className="settings-toggle-name">
                    ACTIVITY LOG
                  </span>

                  <span className="settings-toggle-description">
                    Show the conversation activity log panel
                  </span>

                  <span className="settings-toggle-state">
                    {showActivityLog ? "ON" : "OFF"}
                  </span>

                  <span
                    className={`settings-switch ${
                      showActivityLog
                        ? "settings-switch-on"
                        : "settings-switch-off"
                    }`}
                  >
                    <span className="settings-switch-knob" />
                  </span>

                  <input
                    type="checkbox"
                    checked={showActivityLog}
                    onChange={(event) =>
                      setShowActivityLog(event.target.checked)
                    }
                    className="settings-hidden-checkbox"
                  />
                </label>

                {/* SYSTEM MONITOR */}
                <label className="settings-toggle-row">
                  <span className="settings-toggle-icon">▣</span>

                  <span className="settings-toggle-name">
                    SYSTEM MONITOR
                  </span>

                  <span className="settings-toggle-description">
                    Show the system monitor panel
                  </span>

                  <span className="settings-toggle-state">
                    {showSystemMonitor ? "ON" : "OFF"}
                  </span>

                  <span
                    className={`settings-switch ${
                      showSystemMonitor
                        ? "settings-switch-on"
                        : "settings-switch-off"
                    }`}
                  >
                    <span className="settings-switch-knob" />
                  </span>

                  <input
                    type="checkbox"
                    checked={showSystemMonitor}
                    onChange={(event) =>
                      setShowSystemMonitor(event.target.checked)
                    }
                    className="settings-hidden-checkbox"
                  />
                </label>

                {/* QUICK TOOLS */}
                <label className="settings-toggle-row">
                  <span className="settings-toggle-icon">▦</span>

                  <span className="settings-toggle-name">
                    QUICK TOOLS
                  </span>

                  <span className="settings-toggle-description">
                    Show the quick tools panel
                  </span>

                  <span className="settings-toggle-state">
                    {showQuickTools ? "ON" : "OFF"}
                  </span>

                  <span
                    className={`settings-switch ${
                      showQuickTools
                        ? "settings-switch-on"
                        : "settings-switch-off"
                    }`}
                  >
                    <span className="settings-switch-knob" />
                  </span>

                  <input
                    type="checkbox"
                    checked={showQuickTools}
                    onChange={(event) =>
                      setShowQuickTools(event.target.checked)
                    }
                    className="settings-hidden-checkbox"
                  />
                </label>
              </div>

              {/* ACTIONS */}
              <div className="settings-modal-actions">

                <button
                  type="button"
                  className="settings-modal-button settings-modal-button-primary"
                  onClick={async () => {
                    try {
                      try {
                        const saved =
                          window.localStorage.getItem(
                            "jarvis-pro-settings"
                          );

                        const settings = saved
                          ? JSON.parse(saved)
                          : {};

                        window.localStorage.setItem(
                          "jarvis-pro-settings",
                          JSON.stringify({
                            ...settings,
                            showActivityLog,
                            showSystemMonitor,
                            showQuickTools,
                          })
                        );
                      } catch {}

                      setModal(null);
                    } catch (error) {
                      console.error(
                        "[HUD] Settings save failed:",
                        error
                      );

                      alert(
                        error instanceof Error
                          ? error.message
                          : "Could not save settings."
                      );
                    }
                  }}
                >
                  <span className="settings-button-icon">✓</span>
                  APPLY
                </button>

                <button
                  type="button"
                  className="settings-modal-button"
                  onClick={() => setModal(null)}
                >
                  <span className="settings-button-icon">×</span>
                  CANCEL
                </button>

              </div>
            </div>
          </section>
        </div>
      )}

      {/* =====================================================
          CUSTOMISE ASSISTANT MODAL
          ===================================================== */}
      {modal === "customise" && (
        <div
          className="settings-modal-backdrop"
          onClick={() => setModal(null)}
        >
          <section
            className="settings-modal customise-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="settings-modal-heading">
              <span>⚙</span>
              CUSTOMISE ASSISTANT
            </div>

            <div className="customise-form">
              <label>
                ASSISTANT NAME
                <input
                  type="text"
                  value={assistantName}
                  onChange={(event) => setAssistantName(event.target.value)}
                  placeholder={assistantName || "Assistant"}
                />
              </label>

              <label>
                YOUR NAME
                <span className="settings-field-help">leave blank for default sir / efendim</span>
                <input
                  type="text"
                  value={userName}
                  onChange={(event) => setUserName(event.target.value)}
                  placeholder="e.g. Tony"
                />
              </label>

              <AssistantColourPicker
                value={assistantColour}
                onChange={(c) => {
                  setAssistantColour(c);
                  document.documentElement.style.setProperty("--assistant-colour", c);
                }}
              />

              <div className="settings-modal-actions">
                <button
                  type="button"
                  className="settings-modal-button settings-modal-button-primary"
                  onClick={applyAssistantSettings}
                >
                  APPLY CHANGES
                </button>
                <button
                  type="button"
                  className="settings-modal-button"
                  onClick={() => setModal(null)}
                >
                  CANCEL
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
