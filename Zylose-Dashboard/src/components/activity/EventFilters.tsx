"use client";

import { useState } from "react";
import type { DetectionType } from "@/lib/types";
import { Search } from "lucide-react";

interface EventFiltersProps {
  onFilterChange: (filters: {
    search: string;
    classification: DetectionType | "all";
    device: string;
    minConfidence: number;
    maxConfidence: number;
  }) => void;
}

export function EventFilters({ onFilterChange }: EventFiltersProps) {
  const [search, setSearch] = useState("");
  const [classification, setClassification] = useState<
    DetectionType | "all"
  >("all");
  const [device, setDevice] = useState("all");
  const [minConfidence, setMinConfidence] = useState(0);
  const [maxConfidence, setMaxConfidence] = useState(100);

  const handleChange = (
    key: string,
    value: string | number
  ) => {
    const filters = {
      search,
      classification,
      device,
      minConfidence,
      maxConfidence,
      [key]: value,
    };
    if (key === "search") setSearch(value as string);
    if (key === "classification")
      setClassification(value as DetectionType | "all");
    if (key === "device") setDevice(value as string);
    if (key === "minConfidence") setMinConfidence(value as number);
    if (key === "maxConfidence") setMaxConfidence(value as number);
    onFilterChange(filters);
  };

  return (
    <div className="flex flex-wrap gap-3">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input
          type="text"
          placeholder="Search events..."
          value={search}
          onChange={(e) => handleChange("search", e.target.value)}
          className="w-full h-10 pl-10 pr-4 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[13px] text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 focus:border-indigo-500/30 transition-all"
        />
      </div>

      <select
        value={classification}
        onChange={(e) =>
          handleChange("classification", e.target.value)
        }
        className="h-10 px-3 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[13px] text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 appearance-none cursor-pointer"
      >
        <option value="all" className="bg-[#1a1a1e]">
          All Classifications
        </option>
        <option value="zylose" className="bg-[#1a1a1e]">
          ZYLOSE
        </option>
        <option value="unknown" className="bg-[#1a1a1e]">
          UNKNOWN
        </option>
        <option value="silence" className="bg-[#1a1a1e]">
          SILENCE
        </option>
      </select>

      <select
        value={device}
        onChange={(e) => handleChange("device", e.target.value)}
        className="h-10 px-3 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[13px] text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 appearance-none cursor-pointer"
      >
        <option value="all" className="bg-[#1a1a1e]">
          All Devices
        </option>
        <option value="ZYLOSE-ESP32-01" className="bg-[#1a1a1e]">
          ZYLOSE-ESP32-01
        </option>
      </select>

      <div className="flex items-center gap-2">
        <input
          type="number"
          min={0}
          max={100}
          value={minConfidence}
          onChange={(e) =>
            handleChange("minConfidence", Number(e.target.value))
          }
          className="w-16 h-10 px-3 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[13px] text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500/30"
          placeholder="Min"
        />
        <span className="text-zinc-600 text-[12px]">to</span>
        <input
          type="number"
          min={0}
          max={100}
          value={maxConfidence}
          onChange={(e) =>
            handleChange("maxConfidence", Number(e.target.value))
          }
          className="w-16 h-10 px-3 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[13px] text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500/30"
          placeholder="Max"
        />
      </div>
    </div>
  );
}
