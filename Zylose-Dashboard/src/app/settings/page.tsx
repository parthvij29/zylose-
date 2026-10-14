"use client";

import { AppLayout } from "@/components/layout/AppLayout";
import {
  Settings,
  Cpu,
  Zap,
  Bell,
  Palette,
} from "lucide-react";

export default function SettingsPage() {
  return (
    <AppLayout pathname="/settings">
      <div className="space-y-6">
        <div>
          <p className="text-[13px] text-zinc-500">
            Configure your ZYLOSE device and application preferences.
          </p>
        </div>

        <SettingsSection
          icon={Settings}
          title="General"
          description="Application settings"
        >
          <SettingsRow label="Application Name" value="ZYLOSE" />
          <SettingsRow label="Version" value="1.0.0" />
          <SettingsRow label="Environment" value="Development" />
        </SettingsSection>

        <SettingsSection
          icon={Cpu}
          title="Device"
          description="Device configuration"
        >
          <SettingsRow label="Device Name" value="ZYLOSE-ESP32-01" />
          <SettingsRow label="Model" value="ESP32-WROOM" />
          <SettingsRow label="Firmware" value="v1.0.0" />
          <SettingsRow label="Connection" value="Wi-Fi" />
        </SettingsSection>

        <SettingsSection
          icon={Zap}
          title="Detection"
          description="Detection algorithm parameters"
        >
          <SettingsRow
            label="Minimum Zylose Confidence"
            value="70%"
          />
          <SettingsRow
            label="Zylose / Unknown Margin"
            value="15%"
          />
          <SettingsRow
            label="Sampling Rate"
            value="16000 Hz"
          />
          <SettingsRow
            label="Audio Window"
            value="1 second"
          />
          <div className="mt-3 px-4 py-2.5 rounded-lg bg-amber-500/5 border border-amber-500/10">
            <p className="text-[12px] text-amber-400/80">
              Detection settings are currently read-only. Connect a backend to
              enable configuration.
            </p>
          </div>
        </SettingsSection>

        <SettingsSection
          icon={Bell}
          title="Notifications"
          description="Alert preferences"
        >
          <SettingsRow label="Push Notifications" value="Disabled" />
          <SettingsRow label="Email Alerts" value="Disabled" />
          <SettingsRow label="Webhook URL" value="Not configured" />
        </SettingsSection>

        <SettingsSection
          icon={Palette}
          title="Appearance"
          description="Visual preferences"
        >
          <SettingsRow label="Theme" value="Dark" />
          <SettingsRow label="Accent Color" value="Indigo" />
        </SettingsSection>
      </div>
    </AppLayout>
  );
}

function SettingsSection({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: typeof Settings;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
      <div className="p-5 md:p-6 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-white/[0.04] flex items-center justify-center">
            <Icon className="w-[18px] h-[18px] text-zinc-400" />
          </div>
          <div>
            <h3 className="text-[14px] font-semibold text-white tracking-tight">
              {title}
            </h3>
            <p className="text-[12px] text-zinc-500">{description}</p>
          </div>
        </div>
      </div>
      <div className="divide-y divide-white/[0.04]">{children}</div>
    </div>
  );
}

function SettingsRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between px-5 md:px-6 py-3.5 hover:bg-white/[0.02] transition-colors">
      <span className="text-[13px] text-zinc-400 font-medium">{label}</span>
      <span className="text-[13px] text-zinc-200 font-mono">{value}</span>
    </div>
  );
}
