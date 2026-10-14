"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useApiData, usePolling } from "@/lib/hooks";
import { getDevices } from "@/lib/api";
import { mapDevice } from "@/lib/types";
import type { DeviceInfo } from "@/lib/types";
import {
  Cpu,
  Wifi,
  Mic,
  Zap,
  Clock,
  HardDrive,
  Activity,
  Signal,
} from "lucide-react";

function formatUptime(seconds: number | null): string {
  if (seconds === null) return "Not reported";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

function formatLastSeen(iso: string | null): string {
  if (!iso) return "Never reported";
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 5) return "just now";
  if (secs < 60) return `${secs} seconds ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)} minutes ago`;
  return `${Math.floor(secs / 3600)} hours ago`;
}

export default function DevicesPage() {
  const { data, loading, error, refetch } = useApiData(
    () => getDevices().then((r) => r.devices.map(mapDevice)),
    []
  );

  usePolling(refetch, 10_000, !error);

  const device = data?.[0] || null;

  return (
    <AppLayout pathname="/devices">
      <div className="space-y-6">
        <div>
          <p className="text-[13px] text-zinc-500">
            Manage and monitor your connected devices.
          </p>
        </div>

        {loading && (
          <div className="space-y-6 animate-pulse">
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-64" />
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-48" />
          </div>
        )}

        {error && !loading && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <div>
                <p className="text-[13px] text-red-400 font-medium">Unable to load device data</p>
                <p className="text-[12px] text-zinc-500">{error}</p>
              </div>
            </div>
            <button
              onClick={refetch}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[12px] font-medium text-zinc-300 hover:bg-white/[0.06] transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Try again
            </button>
          </div>
        )}

        {!loading && !error && !device && (
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-16 text-center">
            <p className="text-[13px] text-zinc-500">No devices connected.</p>
          </div>
        )}

        {!loading && !error && device && (
          <>
            <DeviceCard device={device} />
            <DeviceHealth device={device} />
          </>
        )}
      </div>
    </AppLayout>
  );
}

function DeviceCard({ device }: { device: DeviceInfo }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
      <div className="p-6 md:p-8 border-b border-white/[0.06]">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Cpu className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-[17px] font-bold text-white tracking-tight">
                {device.name}
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <div className={`w-2 h-2 rounded-full ${device.status === "online" ? "bg-emerald-400 animate-pulse" : "bg-zinc-500"}`} />
                <span className={`text-[12px] font-medium uppercase tracking-wider ${device.status === "online" ? "text-emerald-400" : "text-zinc-500"}`}>
                  {device.status === "online" ? "Online" : "Offline"}
                </span>
              </div>
            </div>
          </div>

          <span className="px-3 py-1 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[12px] text-zinc-400 font-mono">
            {device.aiModel}
          </span>
        </div>
      </div>

      <div className="p-6 md:p-8">
        <h3 className="text-[13px] font-semibold text-zinc-300 tracking-tight mb-5">
          Device Information
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <DeviceInfoRow icon={Wifi} label="Connection" value={device.connection} />
          <DeviceInfoRow icon={Mic} label="Microphone" value={device.microphone} />
          <DeviceInfoRow icon={Activity} label="Sampling Rate" value={`${device.samplingRate.toLocaleString()} Hz`} />
          <DeviceInfoRow icon={Zap} label="AI Model" value={device.aiModel} />
          <DeviceInfoRow icon={HardDrive} label="Model Input" value={device.modelInput} />
          <DeviceInfoRow icon={Clock} label="Firmware" value={device.firmware} />
          <DeviceInfoRow icon={Clock} label="Last Seen" value={formatLastSeen(device.lastSeen)} />
        </div>
      </div>
    </div>
  );
}

function DeviceHealth({ device }: { device: DeviceInfo }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
      <div className="p-6 md:p-8">
        <h3 className="text-[13px] font-semibold text-zinc-300 tracking-tight mb-5">
          Reported Device Telemetry
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <ReportedMetric
            icon={Clock}
            label="Uptime"
            value={formatUptime(device.uptime)}
          />
          <ReportedMetric
            icon={Signal}
            label="Wi-Fi Signal"
            value={device.wifiSignal === null ? "Not reported" : `${device.wifiSignal} dBm`}
          />
        </div>
        <p className="mt-4 text-[12px] text-zinc-500">
          CPU and memory usage are not collected by the current device API.
        </p>
      </div>
    </div>
  );
}

function DeviceInfoRow({ icon: Icon, label, value }: { icon: typeof Cpu; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
      <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center flex-shrink-0">
        <Icon className="w-4 h-4 text-zinc-400" />
      </div>
      <div>
        <p className="text-[11px] text-zinc-500 uppercase tracking-wider font-medium">{label}</p>
        <p className="text-[13px] text-zinc-200 font-medium">{value}</p>
      </div>
    </div>
  );
}

function ReportedMetric({ icon: Icon, label, value }: { icon: typeof Cpu; label: string; value: string }) {
  return (
    <div className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.04]">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-zinc-400" />
        <span className="text-[11px] text-zinc-500 uppercase tracking-wider font-medium">{label}</span>
      </div>
      <p className="text-[18px] font-bold text-white">{value}</p>
    </div>
  );
}
