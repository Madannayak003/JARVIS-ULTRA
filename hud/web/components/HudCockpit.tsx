"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  HUDState,
} from "@/lib/hudBridge";

import type {
  HUDActivity,
  HUDActivityAction,
  PersonalLinkEntry,
} from "@/app/page";


type Props = {

  state: HUDState;

  activities: HUDActivity[];

  assistantName: string;

  userName: string;

  morningBriefHeadlines: Array<{
    category: string;
    title: string;
    link?: string;
  }>;

  onMorningBriefClose: () => void;

  onCommand: (command: string) => void;

  onActivityAction: (activityId: string, actionId: string, action: string) => void;

  onFullscreen: () => void;

  onSettings: () => void;

  onSchedules: () => void;

  onWorkspace: () => void;

  showActivityLog: boolean;
  showSystemMonitor: boolean;
  showQuickTools: boolean;
};

type GalleryTab = "screenshots" | "captures" | "generated_images" | "recordings";

type GalleryItem = {
  name: string;
  size: number;
  modified_at: number;
  url: string;
  media_type?: string;
};

const GALLERY_DASHBOARD_URL =
  process.env.NEXT_PUBLIC_JARVIS_DASHBOARD_URL ||
  (typeof window !== "undefined"
    ? `http://${window.location.hostname}:8765`
    : "http://127.0.0.1:8765");

type HeaderIconName =
  | "power"
  | "activity"
  | "weather"
  | "news"
  | "music"
  | "screen"
  | "capture"
  | "files"
  | "notes"
  | "settings";

function HeaderIcon({ name }: { name: HeaderIconName }) {
  const common = {
    width: 19,
    height: 19,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  const paths: Record<HeaderIconName, React.ReactNode> = {
    power: <><path d="M12 3v8" /><path d="M7.05 5.93a8 8 0 1 0 9.9 0" /></>,
    activity: <><path d="M3 12h4l2-6 4 12 2-6h6" /><circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" /></>,
    weather: <><circle cx="16.5" cy="7.5" r="3" /><path d="M16.5 2.5v1M16.5 11.5v1M21.5 7.5h-1M12.5 7.5h-1" /><path d="M6 18h10a3 3 0 0 0 .4-5.97A5 5 0 0 0 7 10.5a3.75 3.75 0 0 0-1 7.5Z" /></>,
    news: <><path d="M4 5.5h15a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H5a2 2 0 0 1-2-2v-11a1 1 0 0 1 1-1Z" /><path d="M7 9h9M7 12h9M7 15h5" /><path d="M17 5.5v3" /></>,
    music: <><path d="M9 18V5l10-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="16" cy="16" r="3" /></>,
    screen: <><rect x="3" y="4" width="18" height="13" rx="1.5" /><path d="M8 21h8M12 17v4" /></>,
    capture: <><path d="M4 8h3l1.5-2h7L17 8h3v10H4Z" /><circle cx="12" cy="13" r="3.5" /></>,
    files: <><path d="M5 3h9l4 4v14H5Z" /><path d="M14 3v5h4M8 13h7M8 17h5" /></>,
    notes: <><path d="M6 3h12v18H6z" /><path d="M9 7h6M9 11h6M9 15h4" /><path d="M9 3v2M15 3v2" /></>,
    settings: <><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" /><path d="m19.4 15 .1.1a1.7 1.7 0 0 1-2.4 2.4l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a1.7 1.7 0 0 1-3.4 0v-.2a1.7 1.7 0 0 0-2.9-1.2l-.1.1a1.7 1.7 0 0 1-2.4-2.4l.1-.1a1.7 1.7 0 0 0-1.2-2.9h-.2a1.7 1.7 0 0 1 0-3.4h.2a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a1.7 1.7 0 0 1 2.4-2.4l.1.1a1.7 1.7 0 0 0 2.9-1.2V2a1.7 1.7 0 0 1 3.4 0v.2a1.7 1.7 0 0 0 2.9 1.2l.1-.1a1.7 1.7 0 0 1 2.4 2.4l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a1.7 1.7 0 0 1 0 3.4h-.2a1.7 1.7 0 0 0-1.2 2.9Z" /></>,
  };

  return <svg {...common}>{paths[name]}</svg>;
}


function formatValue(
  value: unknown,
  fallback = "--"
) {

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {

    return fallback;

  }

  return String(value);

}


function formatUptime(
  uptime: unknown,
) {

  if (
    typeof uptime !== "number" ||
    !Number.isFinite(uptime)
  ) {

    return "--:--:--";

  }

  const totalSeconds = Math.floor(uptime);

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor(
    (totalSeconds % 3600) / 60
  );
  const seconds = totalSeconds % 60;

  return [hours, minutes, seconds]
    .map((value) => String(value).padStart(2, "0"))
    .join(":");

}


function SystemInfoCard({
  status,
  uptime,
}: {
  status: unknown;
  uptime: string;
}) {

  const systemStatus = formatValue(
    status,
    "--"
  ).toUpperCase();

  return (
    <div className="cockpit-system-row cockpit-system-info-card">

      <div className="cockpit-system-info-block">

        <span className="cockpit-system-name">
          SYSTEM STATUS
        </span>

        <span className="cockpit-system-state cockpit-system-live-state">
          <span className="cockpit-system-status-dot" />
          {systemStatus}
        </span>

      </div>

      <div className="cockpit-system-info-block">

        <span className="cockpit-system-name">
          UPTIME
        </span>

        <span className="cockpit-system-state cockpit-system-uptime">
          {uptime}
        </span>

      </div>

    </div>
  );

}


function SystemBar({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  const numeric =
    typeof value === "number"
      ? Math.max(0, Math.min(100, value))
      : null;

    const isBattery =
    label === "BAT";

  const isGreen =
    numeric !== null &&
    (
      isBattery
        ? numeric >= 85
        : numeric < 35
    );

  const isYellow =
    numeric !== null &&
    numeric >= 35 &&
    numeric <= 85;

  const isRed =
    numeric !== null &&
    (
      isBattery
        ? numeric < 35
        : numeric > 85
    );

  return (
    <div
      className={
        `cockpit-system-row${
          isGreen
            ? " cockpit-status-green"
            : ""
        }${
          isYellow
            ? " cockpit-status-yellow"
            : ""
        }${
          isRed
            ? " cockpit-status-red"
            : ""
        }`
      }
    >

      <div
        className="cockpit-gauge"
        style={{
          "--gauge-value":
            `${numeric ?? 0}%`,
        } as React.CSSProperties}
      >

        <div
          className="cockpit-gauge-fill"
          style={{
            "--gauge-value":
              `${numeric ?? 0}%`,
          } as React.CSSProperties}
        >

          <div className="cockpit-gauge-center">

            <span className="cockpit-gauge-value">
              {numeric !== null
                ? `${numeric}%`
                : "--"}
            </span>

            <span className="cockpit-gauge-unit">
              LOAD
            </span>

          </div>

        </div>

      </div>

      <div className="cockpit-system-info">

        <span className="cockpit-system-name">
          {label}
        </span>

        <span className="cockpit-system-state">
          {isGreen
            ? "GOOD"
            : isYellow
              ? "MEDIUM"
              : isRed
                ? (isBattery ? "LOW" : "HIGH LOAD")
                : "NOMINAL"}
        </span>

      </div>

    </div>
  );
}


function formatTime(
  timestamp: string
) {

  if (!timestamp) {

    return "--:--:--";

  }

  const date =
    new Date(timestamp);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {

    return timestamp;

  }

  return date.toLocaleTimeString(
    [],
    {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }
  );

}


function ActivityMessage({
  text,
  animate,
}: {
  text: string;
  animate: boolean;
}) {

  const [displayText, setDisplayText] =
    useState(
      animate ? "" : text
    );

  useEffect(() => {

    if (!animate) {

      setDisplayText(text);

      return;

    }

    setDisplayText("");

    let index = 0;

    const interval =
      window.setInterval(() => {

        index += 1;

        setDisplayText(
          text.slice(0, index)
        );

        if (index >= text.length) {

          window.clearInterval(
            interval
          );

        }

      }, 18);

    return () => {

      window.clearInterval(
        interval
      );

    };

  }, [text, animate]);

  return (
    <>
      {displayText}
    </>
  );
}


function PersonalLinksActivity({
  entries,
}: {
  entries: PersonalLinkEntry[];
}) {
  return (
    <div>
      {entries.map((entry) => (
        <div key={entry.url}>
          <a
            href={entry.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(event) => {
              event.preventDefault();
              window.open(entry.url, "_blank", "noopener,noreferrer");
            }}
          >
            {entry.name}: {entry.url}
          </a>
        </div>
      ))}
    </div>
  );
}


export default function HudCockpit({
  state,
  activities,
  assistantName,
  userName,
  morningBriefHeadlines,
  onMorningBriefClose,
  onCommand,
  onActivityAction,
  onFullscreen,
  onSettings,
  onSchedules,
  onWorkspace,
  showActivityLog,
  showSystemMonitor,
  showQuickTools,
}: Props) {

  const system =
    state.system || {};

  // * Live Clock State
  const [currentTime, setCurrentTime] = useState("");
  const [todayDate, setTodayDate] = useState("");
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryTab, setGalleryTab] = useState<GalleryTab>("screenshots");
  const [galleryItems, setGalleryItems] = useState<Record<GalleryTab, GalleryItem[]>>({ screenshots: [], captures: [], generated_images: [], recordings: [] });
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [galleryError, setGalleryError] = useState("");
  const [galleryPreview, setGalleryPreview] = useState<GalleryItem | null>(null);
  const [gallerySaveState, setGallerySaveState] = useState<"" | "saving" | "saved" | "error">("");
  const [galleryDeletePending, setGalleryDeletePending] = useState(false);

  const loadGallery = useCallback(async () => {
    setGalleryLoading(true);
    setGalleryError("");
    try {
      const response = await fetch(`${GALLERY_DASHBOARD_URL}/api/local/gallery`, { cache: "no-store" });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Gallery unavailable.");
      setGalleryItems({
        screenshots: Array.isArray(result.screenshots) ? result.screenshots : [],
        captures: Array.isArray(result.captures) ? result.captures : [],
        generated_images: Array.isArray(result.generated_images) ? result.generated_images : [],
        recordings: Array.isArray(result.recordings) ? result.recordings : [],
      });
    } catch (error) {
      setGalleryError(error instanceof Error ? error.message : "Gallery unavailable.");
    } finally {
      setGalleryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (galleryOpen) void loadGallery();
  }, [galleryOpen, loadGallery]);

  useEffect(() => {
    if (!galleryOpen) return;
    const handleGalleryKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (galleryPreview) {
        setGalleryPreview(null);
        setGallerySaveState("");
      } else {
        setGalleryOpen(false);
      }
    };
    window.addEventListener("keydown", handleGalleryKeyDown);
    return () => window.removeEventListener("keydown", handleGalleryKeyDown);
  }, [galleryOpen, galleryPreview]);

  useEffect(() => {
    if (!galleryOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.classList.add("gallery-open");
    document.body.style.overflow = "hidden";
    return () => {
      document.body.classList.remove("gallery-open");
      document.body.style.overflow = previousOverflow;
    };
  }, [galleryOpen]);

  const saveGalleryFile = async () => {
    if (!galleryPreview || !(window as typeof window & { pywebview?: { api?: { save_gallery_file?: (category: string, filename: string) => Promise<{ ok: boolean; cancelled?: boolean }> } } }).pywebview?.api?.save_gallery_file) {
      setGallerySaveState("error");
      return;
    }
    setGallerySaveState("saving");
    try {
      const result = await (window as typeof window & { pywebview: { api: { save_gallery_file: (category: string, filename: string) => Promise<{ ok: boolean; cancelled?: boolean }> } } }).pywebview.api.save_gallery_file(galleryTab, galleryPreview.name);
      setGallerySaveState(result.cancelled ? "" : result.ok ? "saved" : "error");
    } catch {
      setGallerySaveState("error");
    }
  };

  const deleteGalleryFile = async () => {
    if (!galleryPreview) return;
    try {
      const response = await fetch(`${GALLERY_DASHBOARD_URL}/api/local/gallery/${galleryTab}/${encodeURIComponent(galleryPreview.name)}`, { method: "DELETE" });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error("delete failed");
      setGalleryPreview(null);
      setGalleryDeletePending(false);
      await loadGallery();
    } catch {
      setGallerySaveState("error");
    }
  };

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();

      setCurrentTime(
        now.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );

      setTodayDate(
        now.toLocaleDateString("en-GB", {
          weekday: "short",
          day: "2-digit",
          month: "short",
        })
      );
    };

    updateClock();

    const timer = setInterval(
      updateClock,
      1000
    );

    return () => clearInterval(timer);
  }, []);

  // * Reference for the activity log container
  const activityLogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const log = activityLogRef.current;

    if (!log) {
      return;
    }

    const scrollToLatest = () => {
      log.scrollTop = log.scrollHeight;
    };

    // * Scroll when a new activity arrives.
    requestAnimationFrame(scrollToLatest);

    // * Keep the log pinned to the newest text while
    // * ActivityMessage is typing the response.
    const observer = new MutationObserver(() => {
      requestAnimationFrame(scrollToLatest);
    });

    observer.observe(log, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    return () => {
      observer.disconnect();
    };
  }, [activities]);


  return (

    <div className="hud-cockpit">

      {/* ============================================= */}
      {/* TOP BAR */}
      {/* ============================================= */}

      <header className="cockpit-header">

        {/* ================================================= */}
        {/* BRAND */}
        {/* ================================================= */}

        <div className="cockpit-brand">

          <span className="brand-main">
            {assistantName}
          </span>

          <span className="brand-pro">
            PRO
          </span>

        </div>


        {/* ================================================= */}
        {/* HEADER QUICK NAV */}
        {/* ================================================= */}

        <nav
          className="cockpit-header-nav cockpit-header-nav-left"
          aria-label={`${assistantName} navigation`}
        >

          <button
            type="button"
            onClick={() => onCommand("shutdown")}
          >
            <HeaderIcon name="power" />
            <span>SHUTDOWN</span>
          </button>

          <button
            type="button"
            onClick={() => onCommand("running apps")}
          >
            <HeaderIcon name="activity" />
            <span>RUNNING</span>
          </button>

          <button
            type="button"
            onClick={() => onCommand("weather")}
          >
            <HeaderIcon name="weather" />
            <span>WEATHER</span>
          </button>

          <button
            type="button"
            onClick={() => onCommand("news")}
          >
            <HeaderIcon name="news" />
            <span>NEWS</span>
          </button>

          <button
            type="button"
            onClick={() => onCommand("play music")}
          >
            <HeaderIcon name="music" />
            <span>MUSIC</span>
          </button>

        </nav>


        {/* ================================================= */}
        {/* CENTER TITLE */}
        {/* ================================================= */}

        <div className="cockpit-title">
          {assistantName || "Assistant"}
        </div>


        {/* ================================================= */}
        {/* HEADER TOOLS */}
        {/* ================================================= */}

        <nav
          className="cockpit-header-nav cockpit-header-nav-right"
          aria-label={`${assistantName} tools`}
        >

          <button
            type="button"
            onClick={() => onCommand("what is on my screen")}
          >
            <HeaderIcon name="screen" />
            <span>SCREEN</span>
          </button>

          <button
            type="button"
            onClick={() => onCommand("take photo")}
          >
            <HeaderIcon name="capture" />
            <span>CAPTURE</span>
          </button>

          <button
            type="button"
            onClick={() => onCommand("recent files")}
          >
            <HeaderIcon name="files" />
            <span>FILES</span>
          </button>

          <button
            type="button"
            onClick={() => onCommand("take a note")}
          >
            <HeaderIcon name="notes" />
            <span>NOTES</span>
          </button>

          <button
            type="button"
            onClick={onSettings}
          >
            <HeaderIcon name="settings" />
            <span>SETTINGS</span>
          </button>

        </nav>


        {/* ================================================= */}
        {/* SYSTEM STATUS */}
        {/* ================================================= */}

        <div className="cockpit-system-status">

          <div
            style={{
              display: "flex",
              gap: "8px",
              alignItems: "center",
            }}
          >

            <span className="status-label">
              TIME
            </span>

            <span className="status-value">
              {currentTime || "--:--:--"}
            </span>

          </div>


          <div
            style={{
              display: "flex",
              gap: "8px",
              alignItems: "center",
            }}
          >

            <span className="status-label">
              SYSTEM
            </span>

            <span className="status-value">
              {state.voice_mode
                ?.toUpperCase()
                || "ONLINE"}
            </span>

          </div>

        </div>

      </header>


      {/* ============================================= */}
      {/* LEFT — SYSTEM MONITOR */}
      {/* ============================================= */}

    {showSystemMonitor && (
      <aside className="cockpit-panel cockpit-left">

        <div className="panel-heading">

          <span className="panel-marker">
            ◆
          </span>

          SYSTEM MONITOR

        </div>


        <div className="panel-body">

          <SystemBar
            label="CPU"
            value={system.cpu}
          />

          <SystemBar
            label="RAM"
            value={system.ram}
          />

          <SystemBar
            label="BAT"
            value={system.battery}
          />

          <SystemInfoCard
            status={state.voice_mode}
            uptime={formatUptime(system.uptime)}
          />

        </div>

      </aside>
    )}


      {/* ============================================= */}
      {/* RIGHT — REAL ACTIVITY LOG */}
      {/* ============================================= */}

    {showActivityLog && (
      <aside className="cockpit-panel cockpit-right">

        <div className="panel-heading">

          <span className="panel-marker">
            ◆
          </span>

          ACTIVITY LOG

        </div>

        <div
         ref={activityLogRef}
         className="activity-log">

          {activities.length === 0 ? (

            <div className="activity-empty">

              Waiting for conversation...

            </div>

          ) : (

            activities.map(
              (activity) => (

                <div
                  key={activity.id}
                  className={
                    `activity-message ` +
                    `activity-${activity.speaker}`
                  }
                >

                  <div className="activity-message-meta">

                    <span>
                      {formatTime(
                        activity.timestamp
                      )}
                    </span>

                    <span>

                      {activity.speaker === "user"
                        ? "USER"
                        : activity.speaker === "live"
                          ? `${assistantName} • LIVE`
                          : activity.speaker === "jarvis"
                            ? assistantName
                            : "SYS"}

                    </span>

                  </div>


                  <div className="activity-message-text">

                    {activity.personalLinks?.length ? (
                      <PersonalLinksActivity
                        entries={activity.personalLinks}
                      />
                    ) : (
                      <ActivityMessage
                        text={activity.text}
                        animate={
                          activity.id ===
                          activities[activities.length - 1]?.id
                        }
                      />
                    )}

                    {activity.actions?.length ? (
                      <div className="activity-actions">
                        {activity.actions.map((action: HUDActivityAction) => (
                          <button
                            key={`${action.id}-${action.action}`}
                            type="button"
                            onClick={() => onActivityAction(activity.id, action.id, action.action)}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    ) : null}

                  </div>

                </div>

              )
            )

          )}
          
        </div>

      </aside>
    )}

      {/* ================================================= */}
      {/* QUICK TOOLS */}
      {/* ================================================= */}

    {showQuickTools && (
      <aside className="cockpit-quick-tools">

        {/* <div className="panel-heading">
          <span className="panel-marker">
            ◆
          </span>
          QUICK TOOLS
        </div> */}

        <div className="quick-tools-grid">
          {/* GOOGLE */}
          <button
            type="button"
            onClick={() => onCommand("open google")}
            aria-label="Open Google"
          >
            <span className="quick-tool-icon">
              <svg viewBox="0 0 24 24" width="22" height="22">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 10.03 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                />
              </svg>
            </span>
            <span>GOOGLE</span>
          </button>

          {/* YOUTUBE */}
          <button
            type="button"
            onClick={() => onCommand("open youtube")}
            aria-label="Open YouTube"
          >
            <span className="quick-tool-icon">
              <svg viewBox="0 0 24 24" width="22" height="22">
                <path
                  fill="#FF0000"
                  d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814z"
                />
                <polygon fill="#FFFFFF" points="9.545,15.568 15.818,12 9.545,8.432" />
              </svg>
            </span>
            <span>YOUTUBE</span>
          </button>

          {/* EMAIL */}
          <button
            type="button"
            onClick={() => onCommand("open gmail")}
            aria-label="Open Email"
          >
            <span className="quick-tool-icon">
              <svg viewBox="0 0 24 24" width="22" height="22">
                <path
                  fill="#4285F4"
                  d="M22 6.5v11a2.5 2.5 0 0 1-2.5 2.5H19V8.58l-7 5.25-7-5.25V20H4.5A2.5 2.5 0 0 1 2 17.5v-11a2.5 2.5 0 0 1 3.97-2.02L12 8.94l6.03-4.46A2.5 2.5 0 0 1 22 6.5z"
                />
                <path
                  fill="#EA4335"
                  d="M20 4.5h-2.5L12 8.94 6.5 4.5H4a2.5 2.5 0 0 0-2 1v1l10 7.5 10-7.5v-1a2.5 2.5 0 0 0-2-1z"
                />
              </svg>
            </span>
            <span>EMAIL</span>
          </button>

          {/* GALLERY */}
          <button
            type="button"
            onClick={() => setGalleryOpen(true)}
            aria-label="Open Gallery"
          >
            <span className="quick-tool-icon">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#67e8f9" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="16" rx="2" />
                <circle cx="8.5" cy="9" r="1.5" />
                <path d="m4 17 4.5-4 3.5 3 2.5-2 5.5 4" />
              </svg>
            </span>
            <span>GALLERY</span>
          </button>

          {/* WEBSITES */}
          <button
            type="button"
            onClick={() => onCommand("open website list")}
            aria-label="Open website list"
          >
            <span className="quick-tool-icon">
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="none"
                stroke="#00d4ff"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="2" y1="12" x2="22" y2="12" />
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </span>
            <span>WEBSITES</span>
          </button>

          {/* SCHEDULES */}
          <button
            type="button"
            onClick={onSchedules}
            aria-label="Open Schedules"
          >
            <span className="quick-tool-icon">
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="none"
                stroke="#00e5ff"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="5" width="18" height="16" rx="2" />
                <path d="M16 3v4M8 3v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" />
              </svg>
            </span>
            <span>SCHEDULES</span>
          </button>

          {/* WORKSPACE */}
          <button type="button" onClick={onWorkspace} aria-label="Open Workspace">
            <span className="quick-tool-icon">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#ffbd5a" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 7.5h7l2 2h9v9.5H3z" />
                <path d="M3 7.5V5h7l2 2" />
              </svg>
            </span>
            <span>WORKSPACE</span>
          </button>

          {/* LOCK */}
          <button
            type="button"
            onClick={() => onCommand("lock")}
            aria-label="Lock PC"
          >
            <span className="quick-tool-icon">
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="none"
                stroke="#00e5ff"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="5" y="11" width="14" height="10" rx="2" fill="#00e5ff" fillOpacity="0.15" />
                <path d="M8 11V7a4 4 0 0 1 8 0v4" />
                <circle cx="12" cy="16" r="1.5" fill="#00e5ff" />
              </svg>
            </span>
            <span>LOCK</span>
          </button>
        </div>

      </aside>
    )}

    {galleryOpen && (
      <div className="workspace-center-backdrop hud-gallery-backdrop" onClick={() => { setGalleryOpen(false); setGalleryPreview(null); }}>
        {!galleryPreview && <section className="workspace-center hud-gallery-panel" onClick={(event) => event.stopPropagation()} aria-label="JARVIS Gallery">
          <header className="workspace-center-header hud-gallery-header">
            <strong>JARVIS GALLERY</strong>
            <div>
              <button type="button" className="hud-gallery-refresh" onClick={() => void loadGallery()} aria-label="Refresh gallery" title="Refresh gallery">↻</button>
              <button type="button" onClick={(event) => { event.stopPropagation(); setGalleryOpen(false); setGalleryPreview(null); setGallerySaveState(""); }} aria-label="Close gallery">×</button>
            </div>
          </header>
          <nav className="hud-gallery-tabs" aria-label="Gallery categories">
            {(["screenshots", "captures", "generated_images", "recordings"] as GalleryTab[]).map((tab) => (
              <button key={tab} type="button" className={galleryTab === tab ? "is-active" : ""} onClick={() => { setGalleryTab(tab); setGalleryPreview(null); }}>
                {tab.toUpperCase()}
              </button>
            ))}
          </nav>
          <div className="hud-gallery-content">
            {galleryLoading && <div className="hud-gallery-state">LOADING GALLERY...</div>}
            {!galleryLoading && galleryError && <div className="hud-gallery-state hud-gallery-error">{galleryError}</div>}
            {!galleryLoading && !galleryError && galleryItems[galleryTab].length === 0 && (
              <div className="hud-gallery-state">
                <span className="hud-gallery-empty-icon">▧</span>
                {`NO ${galleryTab.replace("_", " ").toUpperCase()} AVAILABLE`}
              </div>
            )}
            {!galleryLoading && !galleryError && galleryItems[galleryTab].length > 0 && (
              <div className={`hud-gallery-grid hud-gallery-grid--${galleryTab}`}>
                {galleryItems[galleryTab].map((item) => (
                  <button key={item.url} type="button" className="hud-gallery-card" onClick={() => setGalleryPreview(item)}>
                    <div className="hud-gallery-media">
                      {galleryTab !== "recordings" ? (
                        <img src={`${GALLERY_DASHBOARD_URL}${item.url}`} alt={item.name} loading="lazy" />
                      ) : (
                        <video src={`${GALLERY_DASHBOARD_URL}${item.url}`} preload="metadata" />
                      )}
                      {galleryTab === "recordings" && <span className="hud-gallery-play">▶</span>}
                    </div>
                    <span className="hud-gallery-name" title={item.name}>{item.name}</span>
                    <small>{new Date(item.modified_at * 1000).toLocaleString()}</small>
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>}
        {galleryPreview && (
          <div className="workspace-center-backdrop hud-gallery-preview-backdrop" onClick={(event) => { event.stopPropagation(); setGalleryPreview(null); setGallerySaveState(""); }}>
            <div className="workspace-center hud-gallery-preview" onClick={(event) => event.stopPropagation()}>
              <div className="hud-gallery-preview-header">
                <span title={galleryPreview.name}>{galleryPreview.name}</span>
                <button type="button" onClick={(event) => { event.stopPropagation(); setGalleryPreview(null); setGallerySaveState(""); }} aria-label="Close media preview">×</button>
              </div>
              {galleryTab !== "recordings" ? (
                <>
                  <img src={`${GALLERY_DASHBOARD_URL}${galleryPreview.url}`} alt={galleryPreview.name} />
                  <div className="hud-gallery-preview-actions">
                    <button type="button" onClick={() => void saveGalleryFile()} disabled={gallerySaveState === "saving"}>
                      {gallerySaveState === "saving" ? "SAVING..." : "SAVE"}
                    </button>
                    <button type="button" className="hud-gallery-delete" onClick={() => setGalleryDeletePending(true)}>DELETE</button>
                    {gallerySaveState === "saved" && <small>✓ SAVED</small>}
                    {gallerySaveState === "error" && <small className="hud-gallery-copy-error">COULD NOT SAVE</small>}
                  </div>
                </>
              ) : (
                <>
                  {galleryPreview.media_type?.startsWith("audio/") ? <audio src={`${GALLERY_DASHBOARD_URL}${galleryPreview.url}`} controls /> : <video src={`${GALLERY_DASHBOARD_URL}${galleryPreview.url}`} controls preload="metadata" />}
                  <div className="hud-gallery-preview-actions">
                    <button type="button" onClick={() => void saveGalleryFile()} disabled={gallerySaveState === "saving"}>{gallerySaveState === "saving" ? "SAVING..." : "SAVE"}</button>
                    <button type="button" className="hud-gallery-delete" onClick={() => setGalleryDeletePending(true)}>DELETE</button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
        {galleryDeletePending && galleryPreview && (
          <div className="hud-gallery-confirm-backdrop" role="dialog" aria-modal="true" onClick={() => setGalleryDeletePending(false)}>
            <div className="hud-gallery-confirm" onClick={(event) => event.stopPropagation()}>
              <strong>Delete this file?</strong>
              <span>{galleryPreview.name}</span>
              <div className="hud-gallery-preview-actions"><button type="button" onClick={() => setGalleryDeletePending(false)}>CANCEL</button><button type="button" className="hud-gallery-delete" onClick={() => void deleteGalleryFile()}>DELETE</button></div>
            </div>
          </div>
        )}
      </div>
    )}
      
    </div>

  );

}
