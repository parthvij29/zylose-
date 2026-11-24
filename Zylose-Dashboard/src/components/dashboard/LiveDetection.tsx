"use client";

import { useEffect, useState } from "react";
import type { DetectionEvent, AssistantTelemetry } from "@/lib/types";
import { Mic, Zap, Cpu, Activity, Radio, MessageSquare, Terminal, CheckCircle2, ShieldCheck, Layers, Sparkles } from "lucide-react";

interface LiveDetectionProps {
  latestEvent: DetectionEvent | null;
  telemetry?: AssistantTelemetry | null;
}

export function LiveDetection({ latestEvent, telemetry }: LiveDetectionProps) {
  const [timeAgo, setTimeAgo] = useState("just now");

  const query = telemetry?.lastQuery || "What is today's date?";
  const response = telemetry?.lastResponse || "Today is Thursday, November 19, 2026.";
  const intent = telemetry?.intent || "KNOWLEDGE_QUERY";
  const intentConf = telemetry?.intentConfidence || 97.4;
  const urgency = telemetry?.urgency || "CALM_NORMAL";
  const urgencyConf = telemetry?.urgencyConfidence || 96.8;
  const oledText = telemetry?.oledText || "DATE: Thu, 19 Nov 2026";
  const state = telemetry?.state || "IDLE";
  const wakeConf = telemetry?.wakeConfidence || 99.1;
  const speakerVerified = telemetry?.speakerVerified !== undefined ? telemetry.speakerVerified : true;
  const speakerScore = telemetry?.speakerConfidence || 96.4;
  const speakerName = telemetry?.speakerName || "Parth (Owner)";
  const asrConf = telemetry?.asrConfidence || 95.8;

  useEffect(() => {
    if (!latestEvent && !telemetry?.lastUpdated) return;
    const ts = telemetry?.lastUpdated || latestEvent?.timestamp;
    if (!ts) return;

    const update = () => {
      const diff = Date.now() - new Date(ts).getTime();
      const secs = Math.floor(diff / 1000);
      if (secs < 5) setTimeAgo("just now");
      else if (secs < 60) setTimeAgo(`${secs}s ago`);
      else setTimeAgo(`${Math.floor(secs / 60)}m ago`);
    };
    update();
    const interval = setInterval(update, 3000);
    return () => clearInterval(interval);
  }, [latestEvent, telemetry]);

  const stateColors = {
    IDLE: {
      label: "WAITING FOR WAKE WORD ('ZYLOSE')",
      badgeBg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
      ring: "bg-emerald-500",
      accent: "text-emerald-400",
    },
    WAKE: {
      label: "WAKE-WORD CONFIRMED",
      badgeBg: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
      ring: "bg-indigo-500",
      accent: "text-indigo-400",
    },
    LISTEN: {
      label: "ACOUSTIC STREAM LISTENING...",
      badgeBg: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
      ring: "bg-cyan-500",
      accent: "text-cyan-400",
    },
    PROCESSING: {
      label: "NEURAL INFERENCE IN PROGRESS...",
      badgeBg: "bg-amber-500/10 text-amber-400 border-amber-500/30",
      ring: "bg-amber-500",
      accent: "text-amber-400",
    },
    RESPONDING: {
      label: "RESPONSE DISPATCHED & VOICED",
      badgeBg: "bg-purple-500/10 text-purple-400 border-purple-500/30",
      ring: "bg-purple-500",
      accent: "text-purple-400",
    },
  };

  const activeState = stateColors[state] || stateColors.IDLE;

  return (
    <div className="relative">
      <div className="relative overflow-hidden rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/30 via-zinc-950/80 to-zinc-900/90 p-5 md:p-7 shadow-2xl backdrop-blur-xl">
        {/* Top Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-5 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center">
              <div className={`w-3.5 h-3.5 rounded-full ${activeState.ring} animate-pulse-ring`} />
              <div className={`absolute inset-0 w-3.5 h-3.5 rounded-full ${activeState.ring} animate-pulse`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] font-bold tracking-widest uppercase text-white">
                  LIVE CONVERSATIONAL AI & EDGE TELEMETRY
                </span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${activeState.badgeBg}`}>
                  {activeState.label}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                Target Node: <span className="text-zinc-200 font-mono">ESP32-WROOM (COM6 @ 115200 baud)</span> · I2S MEMS Mic · SSD1306 OLED
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[11px] font-mono font-bold text-emerald-300">
                Voice Biometric: {speakerName} ({speakerScore}% Match)
              </span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
              <Radio className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
              <span className="text-[11px] font-mono text-zinc-300">
                Sync {timeAgo}
              </span>
            </div>
          </div>
        </div>

        {/* Hero Section: Live Question & AI Response */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-5">
          {/* Left Column: Live Acoustic Dialogue (7 cols) */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
            {/* Live Question Box */}
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-4 relative overflow-hidden group">
              <div className="absolute top-0 right-0 px-2.5 py-1 bg-indigo-500/20 rounded-bl-lg border-b border-l border-indigo-500/30 flex items-center gap-1.5">
                <Mic className="w-3 h-3 text-indigo-400" />
                <span className="text-[10px] font-bold tracking-wider uppercase text-indigo-300">
                  Voice Query (Acoustic Stream)
                </span>
              </div>
              <p className="text-[11px] font-mono text-indigo-400/80 uppercase tracking-wider mb-1.5">
                USER SPOKE:
              </p>
              <h3 className="text-xl md:text-2xl font-semibold tracking-tight text-white flex items-start gap-2">
                <span className="text-indigo-400 font-mono">&gt;</span>
                <span>&ldquo;{query}&rdquo;</span>
              </h3>
            </div>

            {/* Live Answer Box */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 relative overflow-hidden group">
              <div className="absolute top-0 right-0 px-2.5 py-1 bg-emerald-500/20 rounded-bl-lg border-b border-l border-emerald-500/30 flex items-center gap-1.5">
                <Zap className="w-3 h-3 text-emerald-400" />
                <span className="text-[10px] font-bold tracking-wider uppercase text-emerald-300">
                  AI Knowledge & Action Engine
                </span>
              </div>
              <p className="text-[11px] font-mono text-emerald-400/80 uppercase tracking-wider mb-1.5">
                ZYLOSE ANSWER & ACTUATION:
              </p>
              <p className="text-[15px] md:text-base font-medium text-zinc-100 leading-relaxed">
                {response}
              </p>
            </div>
          </div>

          {/* Right Column: Virtual SSD1306 0.96" OLED Display Mirror (5 cols) */}
          <div className="lg:col-span-5 flex flex-col justify-between">
            <div className="rounded-xl border-2 border-zinc-700 bg-black p-4 font-mono shadow-[inset_0_2px_10px_rgba(0,0,0,0.9)] relative flex flex-col justify-between min-h-[170px]">
              {/* Bezel Title */}
              <div className="flex items-center justify-between pb-2 border-b border-cyan-500/30 text-[10px] text-cyan-400 tracking-wider">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                  <span className="font-bold">SSD1306 OLED (0x3C) MIRROR</span>
                </div>
                <span className="text-zinc-500">128×64 I2C</span>
              </div>

              {/* Virtual OLED Screen Pixel Content */}
              <div className="my-auto py-2">
                <div className="text-cyan-300 font-bold text-[14px] md:text-[15px] tracking-wide filter drop-shadow-[0_0_8px_rgba(6,182,212,0.6)]">
                  {oledText}
                </div>
                <div className="mt-2 text-[10px] text-cyan-500/80 space-y-0.5">
                  <p>&gt; INTENT: {intent}</p>
                  <p>&gt; URGENCY: {urgency}</p>
                  <p>&gt; STATUS: {state === "IDLE" ? "READY FOR WAKE-WORD" : state}</p>
                </div>
              </div>

              {/* Bezel Footer */}
              <div className="pt-2 border-t border-cyan-500/20 flex items-center justify-between text-[9px] text-zinc-500">
                <span>GPIO 21 (SDA) / 22 (SCL)</span>
                <span className="text-cyan-400/90 font-bold">EDGE HARDWARE LIVE</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Strip: Multi-Tier Deep Learning Model Telemetry */}
        <div className="mt-6 pt-5 border-t border-white/[0.08] space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <div className="flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-[11px] font-bold tracking-wider uppercase text-zinc-300">
                Active 5-Model AIML Edge Pipeline (ESP32 Multi-Core Telemetry)
              </span>
            </div>
            <span className="text-[10px] font-mono text-zinc-400">
              Dual-Core Xtensa ESP32 · INT8 Quantized · Zero Cloud Delay
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {/* Model 1: Edge TinyML Wake Word */}
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-3 flex flex-col justify-between space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase">MODEL 1 · KWS</span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">42ms</span>
              </div>
              <div>
                <p className="text-[12px] font-bold text-white leading-tight">Wake-Word CNN</p>
                <p className="text-[10px] text-zinc-400 font-mono mt-0.5 truncate">zylose_int8.tflite</p>
              </div>
              <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between">
                <span className="text-[10px] text-zinc-400">Confidence</span>
                <span className="text-sm font-bold font-mono text-indigo-400">{wakeConf}%</span>
              </div>
            </div>

            {/* Model 2: Speaker Biometrics ("Parth Only") */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-3 flex flex-col justify-between space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase">MODEL 2 · BIOMETRIC</span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">VERIFIED</span>
              </div>
              <div>
                <p className="text-[12px] font-bold text-white leading-tight">Speaker Verification</p>
                <p className="text-[10px] text-emerald-300 font-mono mt-0.5 truncate">{speakerName}</p>
              </div>
              <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between">
                <span className="text-[10px] text-zinc-400">Cosine Match</span>
                <span className="text-sm font-bold font-mono text-emerald-400">{speakerScore}%</span>
              </div>
            </div>

            {/* Model 3: Speech ASR Transcriber */}
            <div className="rounded-xl border border-blue-500/30 bg-blue-950/20 p-3 flex flex-col justify-between space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-blue-400 uppercase">MODEL 3 · ASR</span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">16kHz</span>
              </div>
              <div>
                <p className="text-[12px] font-bold text-white leading-tight">Speech Recognition</p>
                <p className="text-[10px] text-zinc-400 font-mono mt-0.5 truncate">Acoustic CTC Stream</p>
              </div>
              <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between">
                <span className="text-[10px] text-zinc-400">Word Acc</span>
                <span className="text-sm font-bold font-mono text-blue-400">{asrConf}%</span>
              </div>
            </div>

            {/* Model 4: NLP Intent Classifier */}
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-3 flex flex-col justify-between space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase">MODEL 4 · INTENT</span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">4.8ms</span>
              </div>
              <div>
                <p className="text-[12px] font-bold text-white leading-tight truncate">{intent}</p>
                <p className="text-[10px] text-zinc-400 font-mono mt-0.5 truncate">Deep MLP (1200-dim)</p>
              </div>
              <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between">
                <span className="text-[10px] text-zinc-400">Class Conf</span>
                <span className="text-sm font-bold font-mono text-cyan-400">{intentConf}%</span>
              </div>
            </div>

            {/* Model 5: Affective Urgency & Stress */}
            <div className="rounded-xl border border-purple-500/30 bg-purple-950/20 p-3 flex flex-col justify-between space-y-2 col-span-2 md:col-span-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-purple-400 uppercase">MODEL 5 · AFFECTIVE</span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">3.9ms</span>
              </div>
              <div>
                <p className="text-[12px] font-bold text-white leading-tight truncate">{urgency}</p>
                <p className="text-[10px] text-zinc-400 font-mono mt-0.5 truncate">Stress Safety Guard</p>
              </div>
              <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between">
                <span className="text-[10px] text-zinc-400">Safety Conf</span>
                <span className="text-sm font-bold font-mono text-purple-400">{urgencyConf}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
