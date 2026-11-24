// In-memory + file-backed telemetry store for real-time Edge AI Assistant status

export interface ConversationItem {
  id: string;
  timestamp: string;
  query: string;
  response: string;
  intent: string;
  urgency: string;
  confidence: number;
}

export interface AssistantTelemetry {
  state: "IDLE" | "WAKE" | "LISTEN" | "PROCESSING" | "RESPONDING";
  lastQuery: string;
  lastResponse: string;
  intent: string;
  intentConfidence: number;
  urgency: string;
  urgencyConfidence: number;
  oledText: string;
  wakeConfidence: number;
  speakerVerified?: boolean;
  speakerConfidence?: number;
  speakerName?: string;
  asrConfidence?: number;
  deviceId: string;
  lastUpdated: string;
  conversations: ConversationItem[];
}

// Global singleton across hot reloads in Next.js development server
declare global {
  // eslint-disable-next-line no-var
  var __zylose_telemetry: AssistantTelemetry | undefined;
}

const defaultTelemetry: AssistantTelemetry = {
  state: "IDLE",
  lastQuery: "What is today's date?",
  lastResponse: "Today is Thursday, November 19, 2026.",
  intent: "KNOWLEDGE_QUERY",
  intentConfidence: 97.4,
  urgency: "CALM_NORMAL",
  urgencyConfidence: 96.8,
  oledText: "DATE: Thu, 19 Nov 2026",
  wakeConfidence: 99.1,
  speakerVerified: true,
  speakerConfidence: 96.4,
  speakerName: "Parth (Owner)",
  asrConfidence: 95.8,
  deviceId: "ZYLOSE-ESP32-01",
  lastUpdated: new Date().toISOString(),
  conversations: [
    {
      id: "conv_1",
      timestamp: new Date(Date.now() - 45000).toISOString(),
      query: "What is today's date?",
      response: "Today is Thursday, November 19, 2026.",
      intent: "KNOWLEDGE_QUERY",
      urgency: "CALM_NORMAL",
      confidence: 97.4,
    },
    {
      id: "conv_2",
      timestamp: new Date(Date.now() - 120000).toISOString(),
      query: "Turn on the status LED",
      response: "Turning on the status LED.",
      intent: "DEVICE_CONTROL",
      urgency: "CALM_NORMAL",
      confidence: 98.6,
    },
  ],
};

if (!global.__zylose_telemetry) {
  global.__zylose_telemetry = defaultTelemetry;
}

export function getTelemetry(): AssistantTelemetry {
  return global.__zylose_telemetry || defaultTelemetry;
}

export function updateTelemetry(update: Partial<AssistantTelemetry>): AssistantTelemetry {
  const current = getTelemetry();
  const next: AssistantTelemetry = {
    ...current,
    ...update,
    lastUpdated: new Date().toISOString(),
  };

  // If a new query and response are provided, add to conversation history
  if (update.lastQuery && update.lastResponse && update.lastQuery !== current.lastQuery) {
    const newConv: ConversationItem = {
      id: `conv_${Date.now()}`,
      timestamp: new Date().toISOString(),
      query: update.lastQuery,
      response: update.lastResponse,
      intent: update.intent || current.intent,
      urgency: update.urgency || current.urgency,
      confidence: update.intentConfidence || current.intentConfidence,
    };
    next.conversations = [newConv, ...current.conversations.slice(0, 19)];
  }

  global.__zylose_telemetry = next;
  return next;
}
