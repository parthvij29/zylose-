// ── API Contract Types (snake_case, matches backend) ──────────────────────

export type ApiDetectionType = "zylose" | "unknown" | "silence";
export type ApiDetectionStatus = "confirmed" | "rejected" | "detected";

export interface ApiEvent {
  id: string;
  device_id: string;
  timestamp: string;
  result: ApiDetectionType;
  confidence: number;
  unknown_score: number;
  silence_score: number;
  status: ApiDetectionStatus;
}

export interface ApiPagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface ApiEventsResponse {
  events: ApiEvent[];
  pagination: ApiPagination;
}

export interface ApiStats {
  total_zylose: number;
  total_unknown: number;
  total_silence: number;
  total_inferences: number;
  today_zylose: number;
  today_unknown: number;
  today_silence: number;
  average_confidence: number;
  last_detection: string | null;
}

export interface ApiHourlyActivity {
  hour: string;
  zylose: number;
  unknown: number;
  silence: number;
}

export interface ApiAnalytics {
  distribution: {
    zylose: number;
    unknown: number;
    silence: number;
  };
  average_zylose_confidence: number;
  highest_zylose_confidence: number;
  lowest_zylose_confidence: number;
  hourly_activity: ApiHourlyActivity[];
  detection_rate: number;
}

export interface ApiDashboardResponse {
  events: ApiEvent[];
  stats: ApiStats;
  analytics: ApiAnalytics;
}

export interface ApiDevice {
  id: string;
  name: string;
  status: "online" | "offline";
  firmware: string;
  last_seen: string | null;
  connection: string;
  microphone: string;
  sampling_rate: number;
  model: string;
  model_input: string;
  uptime: number | null;
  wifi_signal: number | null;
}

export interface ApiDevicesResponse {
  devices: ApiDevice[];
}

export interface ApiPostEventRequest {
  device_id: string;
  result: ApiDetectionType;
  confidence: number;
  unknown_score: number;
  silence_score: number;
}

// ── UI Types (camelCase, used by components) ──────────────────────────────

export type DetectionType = "zylose" | "unknown" | "silence";
export type DetectionStatus = "confirmed" | "rejected" | "detected";

export interface DetectionEvent {
  id: string;
  timestamp: string;
  deviceId: string;
  type: DetectionType;
  confidence: number;
  silenceScore: number;
  unknownScore: number;
  status: DetectionStatus;
}

export interface DeviceInfo {
  id: string;
  name: string;
  status: "online" | "offline";
  firmware: string;
  lastSeen: string | null;
  connection: string;
  microphone: string;
  samplingRate: number;
  aiModel: string;
  modelInput: string;
  uptime: number | null;
  wifiSignal: number | null;
}

export interface Stats {
  zyloseDetections: number;
  unknownDetections: number;
  silenceDetections: number;
  totalInferences: number;
  todayZylose: number;
  todayUnknown: number;
  todaySilence: number;
  averageConfidence: number;
  lastDetection: string | null;
}

export interface AnalyticsData {
  distribution: {
    type: DetectionType;
    count: number;
    percentage: number;
  }[];
  confidence: {
    average: number;
    highest: number;
    lowest: number;
  };
  hourlyActivity: {
    hour: string;
    zylose: number;
    unknown: number;
    silence: number;
  }[];
  detectionRate: number;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface EventsResponse {
  events: DetectionEvent[];
  pagination: Pagination;
}

// ── Mappers (API → UI) ───────────────────────────────────────────────────

export function mapEvent(api: ApiEvent): DetectionEvent {
  return {
    id: api.id,
    timestamp: api.timestamp,
    deviceId: api.device_id,
    type: api.result,
    confidence: Math.round(api.confidence * 100),
    silenceScore: Math.round(api.silence_score * 100),
    unknownScore: Math.round(api.unknown_score * 100),
    status: api.status,
  };
}

export function mapEventsResponse(api: ApiEventsResponse): EventsResponse {
  return {
    events: api.events.map(mapEvent),
    pagination: {
      page: api.pagination.page,
      limit: api.pagination.limit,
      total: api.pagination.total,
      totalPages: api.pagination.total_pages,
    },
  };
}

export function mapDevice(api: ApiDevice): DeviceInfo {
  return {
    id: api.id,
    name: api.name,
    status: api.status,
    firmware: api.firmware,
    lastSeen: api.last_seen,
    connection: api.connection,
    microphone: api.microphone,
    samplingRate: api.sampling_rate,
    aiModel: api.model,
    modelInput: api.model_input,
    uptime: api.uptime,
    wifiSignal: api.wifi_signal,
  };
}

export function mapStats(api: ApiStats): Stats {
  return {
    zyloseDetections: api.total_zylose,
    unknownDetections: api.total_unknown,
    silenceDetections: api.total_silence,
    totalInferences: api.total_inferences,
    todayZylose: api.today_zylose,
    todayUnknown: api.today_unknown,
    todaySilence: api.today_silence,
    averageConfidence: api.average_confidence,
    lastDetection: api.last_detection,
  };
}

export function mapAnalytics(api: ApiAnalytics): AnalyticsData {
  const total =
    api.distribution.zylose + api.distribution.unknown + api.distribution.silence;
  return {
    distribution: [
      {
        type: "zylose" as DetectionType,
        count: api.distribution.zylose,
        percentage: total > 0 ? Math.round((api.distribution.zylose / total) * 100) : 0,
      },
      {
        type: "unknown" as DetectionType,
        count: api.distribution.unknown,
        percentage: total > 0 ? Math.round((api.distribution.unknown / total) * 100) : 0,
      },
      {
        type: "silence" as DetectionType,
        count: api.distribution.silence,
        percentage: total > 0 ? Math.round((api.distribution.silence / total) * 100) : 0,
      },
    ],
    confidence: {
      average: api.average_zylose_confidence,
      highest: api.highest_zylose_confidence,
      lowest: api.lowest_zylose_confidence,
    },
    hourlyActivity: api.hourly_activity,
    detectionRate: api.detection_rate,
  };
}
