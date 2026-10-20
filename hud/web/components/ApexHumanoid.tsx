"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { HumanoidViewport } from "@/apex/components/HumanoidViewport";
import type { TuningParams } from "@/apex/components/TechnicalDetailsPanel";
import type { MoodState } from "@/apex/utils/humanoidLogic";
import {
  isSoundEnabled,
  playAssemblySoundscape,
  resetAssemblySoundSession,
  stopAllActiveSounds,
  unlockAudioOnUserGesture,
  unlockAudioOnUserGestureAsync,
} from "@/apex/utils/soundEngine";

const DEFAULT_TUNING: TuningParams = {
  boilAmp: 1,
  rimStrength: 0.9,
  dotSharpness: 0.32,
  speakingEnergy: 0.58,
  turnSensitivity: 1,
  compareSplit: 0.5,
  compareMode: "split",
  backdropVisible: true,
};

export default function ApexHumanoid({
  mood,
  onReady,
  onError,
}: {
  mood: MoodState;
  onReady?: () => void;
  onError?: (message: string) => void;
}) {
  const attentionRef = useRef({ x: 0, y: 0 });
  const micEnergyRef = useRef(0);
  const assemblySessionRef = useRef(1);
  const soundPlayedSessionRef = useRef(0);
  const isAssemblingRef = useRef(true);
  const assemblyPctRef = useRef(0);
  const soundOnRef = useRef(isSoundEnabled());
  const [reducedMotion, setReducedMotion] = useState(false);

  const handleAssemblyStatusChange = useCallback((assembling: boolean, pct: number) => {
    isAssemblingRef.current = assembling;
    assemblyPctRef.current = pct;
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(media.matches);
    update();
    media.addEventListener("change", update);
    onReady?.();
    return () => media.removeEventListener("change", update);
  }, [onReady]);

  useEffect(() => {
    const session = assemblySessionRef.current;
    resetAssemblySoundSession(session);

    const tryPlayAssemblySound = async () => {
      unlockAudioOnUserGesture();
      if (
        !soundOnRef.current ||
        !isAssemblingRef.current ||
        assemblyPctRef.current >= 100 ||
        soundPlayedSessionRef.current === session
      ) {
        return false;
      }
      const unlocked = await unlockAudioOnUserGestureAsync();
      if (!unlocked) return false;
      const played = playAssemblySoundscape(session);
      if (played) soundPlayedSessionRef.current = session;
      return played;
    };

    void tryPlayAssemblySound();

    const onFirstGesture = async () => {
      if (await tryPlayAssemblySound()) {
        window.removeEventListener("pointerdown", onFirstGesture);
        window.removeEventListener("keydown", onFirstGesture);
      }
    };
    window.addEventListener("pointerdown", onFirstGesture);
    window.addEventListener("keydown", onFirstGesture);

    return () => {
      window.removeEventListener("pointerdown", onFirstGesture);
      window.removeEventListener("keydown", onFirstGesture);
      stopAllActiveSounds();
    };
  }, []);

  return (
    <div className="apex-humanoid-root" aria-label="APEX humanoid visualizer">
      <HumanoidViewport
        mood={mood}
        effectsEnabled
        reducedMotion={reducedMotion}
        compareActive={false}
        assemblyTrigger={1}
        skipRequested={false}
        shockwaveTrigger={0}
        tuning={DEFAULT_TUNING}
        attentionRef={attentionRef}
        micEnergyRef={micEnergyRef}
        cameraActive={false}
        cameraStatus="off"
        techDetailsOpen={false}
        onDiagnosticsUpdate={() => undefined}
        onAssemblyStatusChange={handleAssemblyStatusChange}
      />
      {onError && null}
    </div>
  );
}
