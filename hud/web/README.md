# JARVIS PRO HUD — UI-1

This is the first UI implementation stage for JARVIS PRO.

## What is included

- The original Ultron Three.js orb engine from the supplied project.
- Original MediaPipe hand tracking implementation.
- Mouse drag rotation.
- Mouse wheel zoom.
- Keyboard `R`, `+`, `-`, `G` controls.
- Hand pinch rotation and two-hand zoom.
- Bloom, scanlines, grain, vignette, floating code, debris and animated core.
- JARVIS PRO identity overlay.

## Run

```powershell
npm install
npm run dev
```

Open the local Next.js address shown in the terminal.

## Important

This stage intentionally does NOT implement the Mark XLIX side panels or Python HUD event bridge yet. Those are UI-2 and UI-3. The goal of UI-1 is to prove that the actual Ultron engine is running inside the JARVIS PRO HUD foundation before we connect the rest of JARVIS PRO.
