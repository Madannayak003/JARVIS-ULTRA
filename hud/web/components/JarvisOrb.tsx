"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import type { OrbSceneApi } from "@/lib/orbScene";

import {
  createOrbScene,
} from "@/lib/orbScene";

import {
  HandTracker,
  type TrackerStatus,
} from "@/lib/handTracker";

type CameraState =
  | "off"
  | "starting"
  | "on"
  | "error";

type UltronColor = {
  name: string;
  value: number;
};

type SceneApi =
  OrbSceneApi & {
    setUltronColor?: (color: number) => void;
  };

// * =====================================================
// * TRACKER MODE LABELS
// * =====================================================

const MODE_LABEL: Record<
  TrackerStatus["mode"],
  string
> = {
  idle: "STANDBY",
  spin: "SPIN",
  zoom: "ZOOM",
};

// * =====================================================
// * ULTRON COLOR PRESETS
// * =====================================================

const ULTRON_COLORS: UltronColor[] = [

  {
    name: "RED",
    value: 0xff2020,
  },

  {
    name: "ORANGE",
    value: 0xff7a20,
  },

  {
    name: "BLUE",
    value: 0x2080ff,
  },

  {
    name: "CYAN",
    value: 0x20eaff,
  },

  {
    name: "PURPLE",
    value: 0x9b30ff,
  },

  {
    name: "GREEN",
    value: 0x20ff80,
  },

];


export default function JarvisOrb({
}: {
}) {

  const containerRef =
    useRef<HTMLDivElement>(null);

  const videoRef =
    useRef<HTMLVideoElement>(null);

  const overlayRef =
    useRef<HTMLCanvasElement>(null);

  const sceneRef =
    useRef<SceneApi | null>(null);

  const trackerRef =
    useRef<HandTracker | null>(null);


  // * ===================================================
  // * STATE
  // * ===================================================

  const [camera, setCamera] =
    useState<CameraState>("off");


  const [status, setStatus] =
    useState<TrackerStatus>({
      hands: 0,
      mode: "idle",
    });


  const [error, setError] =
    useState<string | null>(null);



  const [ultronColor, setUltronColor] =
    useState<number>(
      ULTRON_COLORS[0].value
    );


  const [controlsVisible, setControlsVisible] =
    useState(true);

  // * =====================================================
  // * AVATAR INITIALIZATION / SWITCHING
  // * =====================================================

  useEffect(() => {

    const container =
      containerRef.current;

    if (!container) {
      return;
    }


    let scene: SceneApi;

    scene = createOrbScene(container);

    sceneRef.current =
      scene;

    // * ---------------------------------------------------
    // * Apply current ULTRON color
    // * ---------------------------------------------------

    scene.setUltronColor(ultronColor);

    // * ---------------------------------------------------
    // * Apply current EXPRESSIVE situation
    // * ---------------------------------------------------


    // * ---------------------------------------------------
    // * Cleanup
    // * ---------------------------------------------------

    return () => {

      scene.dispose();

      if (
        sceneRef.current === scene
      ) {

        sceneRef.current =
          null;

      }

    };

  }, [
    ultronColor,
  ]);


  // * =====================================================
  // * =====================================================
  // * APPLY ULTRON COLOR
  // * =====================================================
  //
  // ! IMPORTANT:
  // * Changing the color does NOT recreate the scene.
  // * It directly updates the existing ULTRON orb.
  // * =====================================================

  useEffect(() => {

    sceneRef.current?.setUltronColor?.(
      ultronColor
    );

  }, [
    ultronColor,
  ]);


  // * =====================================================
  // * CHANGE ULTRON COLOR
  // * =====================================================

  const changeUltronColor =
    useCallback(
      (color: number) => {

        setUltronColor(
          color
        );

      },
      []
    );


  // * =====================================================
  // * STOP GESTURES
  // * =====================================================

  const stopGestures =
    useCallback(() => {

      trackerRef.current?.stop();

      trackerRef.current =
        null;


      setCamera(
        "off"
      );


      setStatus({
        hands: 0,
        mode: "idle",
      });

    }, []);


  // * =====================================================
  // * START GESTURES
  // * =====================================================

  const startGestures =
    useCallback(
      async () => {

        const video =
          videoRef.current;

        const overlay =
          overlayRef.current;


        if (
          !video ||
          !overlay ||
          trackerRef.current
        ) {

          return;

        }


        setCamera(
          "starting"
        );


        setError(
          null
        );


        const tracker =
          new HandTracker(
            video,
            overlay,
            {

              onRotate: (
                dt,
                dp
              ) => {

                sceneRef.current?.rotateBy(
                  dt,
                  dp
                );

              },


              onZoom: (
                factor
              ) => {

                sceneRef.current?.zoomBy(
                  factor
                );

              },


              onStatus:
                setStatus,

            }
          );


        trackerRef.current =
          tracker;


        try {

          await tracker.start();

          setCamera(
            "on"
          );

        }

        catch (err) {

          trackerRef.current =
            null;


          tracker.stop();


          setCamera(
            "error"
          );


          const name = err instanceof DOMException ? err.name : "";
          const message = err instanceof Error ? err.message : String(err);
          setError(
            name === "NotAllowedError"
              ? "CAMERA ACCESS DENIED"
              : name === "NotFoundError"
                ? "NO CAMERA FOUND"
                : name === "NotReadableError"
                  ? "CAMERA IS BUSY"
                  : message.startsWith("MODEL_LOAD_FAILED")
                    ? "HAND MODEL LOAD FAILED"
                    : message === "CAMERA_API_UNAVAILABLE"
                      ? "CAMERA API UNAVAILABLE"
                      : "TRACKING INIT FAILED"
          );

        }

      },
      []
    );


  // * =====================================================
  // * GESTURE TOGGLE
  // * =====================================================

  const toggleGestures =
    useCallback(() => {

      if (
        trackerRef.current
      ) {

        stopGestures();

      }

      else {

        void startGestures();

      }

    }, [
      startGestures,
      stopGestures,
    ]);


  // * =====================================================
  // * KEYBOARD CONTROLS
  // * =====================================================

  useEffect(() => {

    const onKey =
      (
        e: KeyboardEvent
      ) => {

        const target = e.target as HTMLElement | null;

        if (
          target instanceof HTMLInputElement ||
          target instanceof HTMLTextAreaElement ||
          target instanceof HTMLSelectElement ||
          target?.isContentEditable
        ) {

          return;

        }

        switch (
          e.key
        ) {

          case "+":
          case "=":

            sceneRef.current?.zoomIn();

            break;


          case "-":
          case "_":

            sceneRef.current?.zoomOut();

            break;


          case "r":
          case "R":

            sceneRef.current?.resetView();

            break;


          case "g":
          case "G":

            toggleGestures();

            break;

        }

      };


    window.addEventListener(
      "keydown",
      onKey
    );


    return () => {

      window.removeEventListener(
        "keydown",
        onKey
      );

    };

  }, [
    toggleGestures,
  ]);


  // * =====================================================
  // * CAMERA STATE
  // * =====================================================

  const cameraOn =
    camera === "on";


  // * =====================================================
  // * RENDER
  // * =====================================================

  return (

    <main className="jarvis-hud">


      {/* ================================================= */}
      {/* ULTRON / JARVIS AVATAR */}
      {/* ================================================= */}

      <div
        ref={containerRef}
        className="orb-root"
      />


      {/* ================================================= */}
      {/* VISUAL OVERLAYS */}
      {/* ================================================= */}

      <div
        className="overlay-vignette"
      />

      <div
        className="overlay-grain"
      />

      <div
        className="overlay-scanlines"
      />


      {/* ================================================= */}
      {/* CONTROL HINT */}
      {/* ================================================= */}

      {/* <div className="hud hud-hint">

        <div>

          <span className="key">
            DRAG
          </span>

          {" "}
          spin
          &nbsp;&nbsp;

          <span className="key">
            SCROLL
          </span>

          {" "}
          zoom

        </div>


        <div>

          {cameraOn ? (

            <>

              <span className="key">
                PINCH + MOVE
              </span>

              {" "}
              spin
              &nbsp;&nbsp;

              <span className="key">
                2 HANDS
              </span>

              {" "}
              zoom

            </>

          ) : (

            <>

              <span className="key">
                G
              </span>

              {" "}
              gestures
              &nbsp;&nbsp;

              <span className="key">
                R
              </span>

              {" "}
              reset
              &nbsp;&nbsp;

              <span className="key">
                +/−
              </span>

              {" "}
              zoom

            </>

          )}

        </div>

      </div> */}


      {/* ================================================= */}
      {/* HUD CONTROLS */}
      {/* ================================================= */}

      <div className="hud hud-controls">

        {/* ================================================= */}
        {/* CAMERA PANEL */}
        {/* ================================================= */}

        <div
          className={
            `camera-panel${
              cameraOn
                ? " visible"
                : ""
            }`
          }
        >

          {/* View finder corners */}

          <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-[var(--assistant-colour)] pointer-events-none z-10" />

          <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-[var(--assistant-colour)] pointer-events-none z-10" />

          <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-[var(--assistant-colour)] pointer-events-none z-10" />

          <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-[var(--assistant-colour)] pointer-events-none z-10" />


          {/* Camera */}

          <video
            ref={videoRef}
            muted
            playsInline
            className="camera-video"
          />

          <canvas
            ref={overlayRef}
            width={208}
            height={156}
            className="camera-overlay"
          />


          {/* Camera status */}

          <div className="camera-status flex items-center justify-between">

            <span className="flex items-center gap-1.5">

              <span
                className={
                  `w-1.5 h-1.5 rounded-full ${
                    status.hands > 0
                      ? "bg-[#00ff66] shadow-[0_0_6px_#00ff66]"
                      : "bg-[var(--assistant-colour)] opacity-60"
                  }`
                }
              />

              {status.hands > 0
                ? `${status.hands} HAND${
                    status.hands > 1
                      ? "S"
                      : ""
                  } · ${
                    MODE_LABEL[status.mode]
                  }`
                : "SCANNING"}

            </span>

          </div>

        </div>


        {/* ================================================= */}
        {/* ERROR */}
        {/* ================================================= */}

        {error && (

          <div className="hud-error">
            {error}
          </div>

        )}


      {controlsVisible && (
        <>
          {/* GESTURE CONTROL */}

          <div
            className="hud-row"
            style={{
              marginBottom: "8px",
            }}
          >
            <button
              type="button"
              className="hud-btn"
              aria-pressed={cameraOn}
              onClick={toggleGestures}
              disabled={camera === "starting"}
            >
              {camera === "starting"
                ? "INITIALIZING…"
                : cameraOn
                  ? "● GESTURES ON"
                  : "○ GESTURES OFF"}
            </button>
          </div>


          {/* ZOOM CONTROLS */}

          <div
            className="hud-row"
            style={{
              display: "flex",
              gap: "8px",
              marginBottom: "10px",
            }}
          >
            <button
              type="button"
              className="hud-btn"
              onClick={() =>
                sceneRef.current?.zoomIn()
              }
              aria-label="Zoom in"
            >
              +
            </button>

            <button
              type="button"
              className="hud-btn"
              onClick={() =>
                sceneRef.current?.zoomOut()
              }
              aria-label="Zoom out"
            >
              −
            </button>

            <button
              type="button"
              className="hud-btn"
              onClick={() =>
                sceneRef.current?.resetView()
              }
            >
              RESET
            </button>
          </div>
        </>
      )} 

        {/* ================================================= */}
        {/* ORB CONTROLS */}
        {/* ================================================= */}
      
      {controlsVisible && (
        <div
          className="hud-orb-controls"
          style={{
            width: "100%",
            marginTop: "2px",
          }}
        >

          {/* ================================================= */}
          {/* ULTRON COLOR CONTROLS */}
          {/* ================================================= */}
          {(
            <div
              className="ultron-color-panel"
              aria-label="ULTRON color selection"
            >
              {/* COLOR TITLE */}
              <div className="ultron-color-title-wrap">
                <span className="ultron-color-label">
                </span>
              </div>

              {/* COLORS — 2 PER ROW */}
              <div className="ultron-color-row">
                {ULTRON_COLORS.map((color) => {
                  const active = ultronColor === color.value;
                  const hex = `#${color.value.toString(16).padStart(6, "0")}`;

                  return (
                    <button
                      key={color.name}
                      type="button"
                      className={`hud-btn ultron-color-btn${active ? " active" : ""}`}
                      aria-label={`ULTRON color ${color.name}`}
                      aria-pressed={active}
                      title={color.name}
                      onClick={() => changeUltronColor(color.value)}
                    >
                      <span
                        className="ultron-color-dot"
                        style={{
                          backgroundColor: hex,
                          boxShadow: active ? `0 0 6px ${hex}` : `0 0 2px ${hex}`,
                        }}
                      />
                      <span className="ultron-color-name">
                        {color.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

        </div>
        
      )}

        {/* ================================================= */}
        {/* CONTROL / MODEL MODE */}
        {/* ================================================= */}

        <div
          className="hud-row"
          style={{
            display: "flex",
            gap: "8px",
            marginBottom: "5px",
          }}
        >

          <button
            type="button"
            className="hud-btn hud-controls-toggle"
            style={{
              borderRadius: "30px",
            }}
            aria-pressed={controlsVisible}
            onClick={() => setControlsVisible((visible) => !visible)}
          >
            {controlsVisible
              ? "● CONTROLS"
              : "○ CONTROLS"}
          </button>
          
        </div>

      </div>

    </main>

  );

}
