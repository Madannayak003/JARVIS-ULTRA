import React from 'react';
import { MoodState } from '../utils/humanoidLogic';

export interface TuningParams {
  boilAmp: number;
  rimStrength: number;
  dotSharpness: number;
  speakingEnergy: number;
  turnSensitivity: number;
  compareSplit: number;
  compareMode: 'split' | 'side-by-side' | 'overlay';
  backdropVisible: boolean;
}

export interface DiagnosticsSnapshot {
  fps: number;
  totalParticles: number;
  frontParticles: number;
  backParticles: number;
  dustParticles: number;
  boilParticles: number;
  backdropParticles: number;
  assemblyParticles: number;
  yawDeg: number;
  pitchDeg: number;
  bloomRadius: number;
  moodA: MoodState;
  moodB: MoodState;
  assemblyPct: number;
  shockwaveActive: boolean;
  cameraStatus: string;
}

interface TechnicalDetailsPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  diagnostics: DiagnosticsSnapshot;
  tuning: TuningParams;
  onChangeTuning: (next: Partial<TuningParams>) => void;
  onResetTuning: () => void;
  onTriggerShockwave: () => void;
  compareActive: boolean;
}

export const TechnicalDetailsPanel: React.FC<TechnicalDetailsPanelProps> = ({
  isOpen,
  onToggle,
  diagnostics,
  tuning,
  onChangeTuning,
  onResetTuning,
  onTriggerShockwave,
  compareActive,
}) => {
  return (
    <aside
      aria-label="Technical Details and Diagnostics"
      className="fixed top-3 right-3 sm:top-4 sm:right-4 z-40 flex flex-col items-end pointer-events-auto"
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        className="min-h-[38px] sm:min-h-[40px] px-2.5 sm:px-3.5 py-1.5 rounded-lg border border-[#00E5FF]/40 bg-[#050608]/90 text-[#00E5FF] text-[10px] sm:text-xs tracking-widest uppercase hover:border-[#00E5FF] hover:bg-[#0a141c] transition-colors cursor-pointer whitespace-nowrap inline-flex items-center gap-1.5"
      >
        <span>{isOpen ? '[-]' : '[+]'}</span>
        <span>{isOpen ? 'Hide Technical Details' : 'Technical Details'}</span>
      </button>

      {isOpen && (
        <div
          data-testid="technical-details-panel"
          className="mt-2 w-[330px] max-w-[92vw] max-h-[76vh] overflow-y-auto rounded-xl border border-[#00E5FF]/35 bg-[#050608]/95 p-4 text-[#C8F7FF] shadow-2xl space-y-4 text-xs"
        >
          <div className="flex items-center justify-between border-b border-[#00E5FF]/20 pb-2">
            <span className="text-[#00E5FF] font-semibold tracking-widest uppercase">
              Particle Telemetry
            </span>
            <span className="tabular-nums text-[#FFB733]">{diagnostics.fps} FPS</span>
          </div>

          <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 tabular-nums text-[11px] text-[#C8F7FF]/85">
            <div>Total 3D Points:</div>
            <div className="text-right text-[#00E5FF]">
              {diagnostics.totalParticles.toLocaleString()}
            </div>
            <div>Front Contour Shell:</div>
            <div className="text-right">{diagnostics.frontParticles.toLocaleString()}</div>
            <div>Back Occlusion Shell:</div>
            <div className="text-right">{diagnostics.backParticles.toLocaleString()}</div>
            <div>Interior Head Volume:</div>
            <div className="text-right">{diagnostics.dustParticles.toLocaleString()}</div>
            <div>Silhouette Edge Boil:</div>
            <div className="text-right">{diagnostics.boilParticles.toLocaleString()}</div>
            <div>Backdrop Ridge Points:</div>
            <div className="text-right">{diagnostics.backdropParticles.toLocaleString()}</div>
            <div>Assembly Bézier Motes:</div>
            <div className="text-right">{diagnostics.assemblyParticles.toLocaleString()}</div>
            <div>Head Yaw / Pitch:</div>
            <div className="text-right">
              {diagnostics.yawDeg.toFixed(1)}° / {diagnostics.pitchDeg.toFixed(1)}°
            </div>
            <div>Radial Blend Radius:</div>
            <div className="text-right">
              {diagnostics.bloomRadius >= 8.9
                ? 'SETTLED'
                : `${diagnostics.bloomRadius.toFixed(2)} NDC`}
            </div>
            <div>State Transition:</div>
            <div className="text-right uppercase">
              {diagnostics.moodA} → {diagnostics.moodB}
            </div>
          </div>

          {compareActive && (
            <div className="border-t border-[#00E5FF]/20 pt-3 space-y-2">
              <div className="text-[#FFB733] uppercase tracking-wider text-[11px]">
                Stage 2 · Source Comparison Mode
              </div>
              <div className="flex gap-1.5">
                {(['split', 'side-by-side', 'overlay'] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => onChangeTuning({ compareMode: m })}
                    className={`flex-1 py-1 px-2 rounded border text-[10px] uppercase tracking-wider cursor-pointer whitespace-nowrap ${
                      tuning.compareMode === m
                        ? 'border-[#00E5FF] bg-[#00E5FF]/20 text-[#C8F7FF]'
                        : 'border-[#00E5FF]/25 bg-transparent text-[#C8F7FF]/70'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
              {tuning.compareMode === 'split' && (
                <label className="block space-y-1">
                  <div className="flex justify-between text-[11px]">
                    <span>Split Wipe Position</span>
                    <span className="tabular-nums">{Math.round(tuning.compareSplit * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0.05}
                    max={0.95}
                    step={0.01}
                    value={tuning.compareSplit}
                    onChange={(e) => onChangeTuning({ compareSplit: parseFloat(e.target.value) })}
                    className="w-full accent-[#00E5FF]"
                  />
                </label>
              )}
            </div>
          )}

          <div className="border-t border-[#00E5FF]/20 pt-3 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[#00E5FF] uppercase tracking-wider text-[11px]">
                Shader & Motion Tuning
              </span>
              <button
                type="button"
                onClick={onResetTuning}
                className="text-[10px] text-[#FFB733] hover:underline uppercase cursor-pointer"
              >
                Reset Defaults
              </button>
            </div>

            <label className="block space-y-1">
              <div className="flex justify-between text-[11px]">
                <span>Edge Boil Amplitude</span>
                <span className="tabular-nums">{tuning.boilAmp.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min={0}
                max={2.5}
                step={0.05}
                value={tuning.boilAmp}
                onChange={(e) => onChangeTuning({ boilAmp: parseFloat(e.target.value) })}
                className="w-full accent-[#00E5FF]"
              />
            </label>

            <label className="block space-y-1">
              <div className="flex justify-between text-[11px]">
                <span>Silhouette Rim Highlight</span>
                <span className="tabular-nums">{tuning.rimStrength.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0}
                max={2.0}
                step={0.05}
                value={tuning.rimStrength}
                onChange={(e) => onChangeTuning({ rimStrength: parseFloat(e.target.value) })}
                className="w-full accent-[#00E5FF]"
              />
            </label>

            <label className="block space-y-1">
              <div className="flex justify-between text-[11px]">
                <span>Particle Dot Sharpness</span>
                <span className="tabular-nums">{tuning.dotSharpness.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.48}
                step={0.01}
                value={tuning.dotSharpness}
                onChange={(e) => onChangeTuning({ dotSharpness: parseFloat(e.target.value) })}
                className="w-full accent-[#00E5FF]"
              />
            </label>

            <label className="block space-y-1">
              <div className="flex justify-between text-[11px]">
                <span>Speaking Wave Energy</span>
                <span className="tabular-nums">{Math.round(tuning.speakingEnergy * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.1}
                max={1.0}
                step={0.02}
                value={tuning.speakingEnergy}
                onChange={(e) => onChangeTuning({ speakingEnergy: parseFloat(e.target.value) })}
                className="w-full accent-[#FFB733]"
              />
            </label>

            <label className="block space-y-1">
              <div className="flex justify-between text-[11px]">
                <span>Head Turn Sensitivity</span>
                <span className="tabular-nums">{tuning.turnSensitivity.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min={0}
                max={1.75}
                step={0.05}
                value={tuning.turnSensitivity}
                onChange={(e) => onChangeTuning({ turnSensitivity: parseFloat(e.target.value) })}
                className="w-full accent-[#00E5FF]"
              />
            </label>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-[11px] cursor-pointer">
                <input
                  type="checkbox"
                  checked={tuning.backdropVisible}
                  onChange={(e) => onChangeTuning({ backdropVisible: e.target.checked })}
                  className="accent-[#00E5FF]"
                />
                <span>Stage 6 Atmospheric Backdrop</span>
              </label>
              <button
                type="button"
                onClick={onTriggerShockwave}
                className="px-2.5 py-1 rounded border border-[#FFB733]/50 bg-[#FFB733]/10 text-[#FFB733] text-[10px] uppercase tracking-wider hover:bg-[#FFB733]/20 cursor-pointer whitespace-nowrap"
              >
                Pulse Wave
              </button>
            </div>
          </div>

          <div className="border-t border-[#00E5FF]/20 pt-2.5 text-[10px] leading-relaxed text-[#C8F7FF]/65">
            <div>
              <strong className="text-[#00E5FF]">Color Pipeline:</strong> Un-tonemapped sRGB plate
              sampling (NoToneMapping) prevents double gamma conversion.
            </div>
            <div>
              <strong className="text-[#00E5FF]">Stages 1–9:</strong> Reference Plates · Particle
              Sampling · Radial Moods · Cubic-Bézier Assembly (25%/60%) · Revolve Depth Head Turn ·
              Mountain Vein Backdrop · Face-Origin Shockwave · Chest Breathing.
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
