"use client";

import { useEffect, useState } from "react";

export type PhoneCallState = {
  state: "outgoing" | "ringing" | "active" | "disconnected";
  direction: "OUTGOING" | "INCOMING" | "";
  caller_name: string;
  phone_number: string;
  started_at?: number | string | null;
};

function timestampSeconds(value: PhoneCallState["started_at"]): number {
  if (typeof value === "number") return value > 10_000_000_000 ? value / 1000 : value;
  if (typeof value === "string") {
    const numeric = Number(value);
    if (Number.isFinite(numeric)) return numeric > 10_000_000_000 ? numeric / 1000 : numeric;
    const parsed = Date.parse(value);
    if (Number.isFinite(parsed)) return parsed / 1000;
  }
  return 0;
}

function formatDuration(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60).toString().padStart(2, "0");
  const remainder = (total % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}

export default function PhoneCallIsland({ call }: { call: PhoneCallState }) {
  const [elapsed, setElapsed] = useState(() => {
    const started = timestampSeconds(call.started_at);
    return started && call.state === "active" ? Date.now() / 1000 - started : 0;
  });

  useEffect(() => {
    const started = timestampSeconds(call.started_at);
    if (call.state !== "active" || !started) {
      if (call.state !== "disconnected") setElapsed(0);
      return;
    }

    const update = () => setElapsed(Math.max(0, Date.now() / 1000 - started));
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [call.state, call.started_at]);

  const isIncoming = call.direction === "INCOMING" || call.state === "ringing";
  const label =
    call.state === "outgoing"
      ? "CALLING"
      : call.state === "active"
        ? "● CALL ACTIVE"
        : call.state === "disconnected"
          ? "CALL ENDED"
          : isIncoming
            ? "INCOMING CALL"
            : "CALLING";
  const displayName = call.caller_name.trim();
  const displayNumber = call.phone_number.trim();

  return (
    <aside
      className={`phone-call-island phone-call-island-${call.state}`}
      aria-live="polite"
      aria-label="Phone call status"
    >
      <div className="phone-call-island-status">
        {call.state === "active" && <span className="phone-call-island-dot" />}
        <span>{label}</span>
      </div>
      {displayName && <div className="phone-call-island-name">{displayName}</div>}
      {displayNumber && <div className="phone-call-island-number">{displayNumber}</div>}
      {call.state === "active" && (
        <div className="phone-call-island-duration">{formatDuration(elapsed)}</div>
      )}
      {call.state === "disconnected" && elapsed > 0 && (
        <div className="phone-call-island-duration">{formatDuration(elapsed)}</div>
      )}
    </aside>
  );
}
