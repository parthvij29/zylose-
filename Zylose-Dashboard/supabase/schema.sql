-- ZYLOSE Database Schema
-- Run this in your Supabase SQL Editor (https://supabase.com/dashboard → SQL Editor)

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'offline' CHECK (status IN ('online', 'offline')),
  firmware      TEXT NOT NULL DEFAULT 'v1.0.0',
  last_seen     TIMESTAMPTZ,
  connection    TEXT NOT NULL DEFAULT 'Wi-Fi',
  microphone    TEXT NOT NULL DEFAULT 'INMP441',
  sampling_rate INTEGER NOT NULL DEFAULT 16000,
  model         TEXT NOT NULL DEFAULT 'ZYLOSE INT8',
  model_input   TEXT NOT NULL DEFAULT '98 × 13',
  uptime        INTEGER,
  wifi_signal   INTEGER,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Keep telemetry nullable for devices that have not reported these values.
ALTER TABLE devices ALTER COLUMN uptime DROP NOT NULL;
ALTER TABLE devices ALTER COLUMN uptime DROP DEFAULT;
ALTER TABLE devices ALTER COLUMN wifi_signal DROP NOT NULL;
ALTER TABLE devices ALTER COLUMN wifi_signal DROP DEFAULT;

-- Sequence for event IDs
CREATE SEQUENCE IF NOT EXISTS events_id_seq START 1;

-- Events table
CREATE TABLE IF NOT EXISTS events (
  id            TEXT PRIMARY KEY DEFAULT ('evt_' || lpad(nextval('events_id_seq')::text, 6, '0')),
  device_id     TEXT NOT NULL REFERENCES devices(id),
  timestamp     TIMESTAMPTZ NOT NULL DEFAULT now(),
  result        TEXT NOT NULL CHECK (result IN ('zylose', 'unknown', 'silence')),
  confidence    NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  unknown_score NUMERIC(5,4) NOT NULL DEFAULT 0 CHECK (unknown_score >= 0 AND unknown_score <= 1),
  silence_score NUMERIC(5,4) NOT NULL DEFAULT 0 CHECK (silence_score >= 0 AND silence_score <= 1),
  status        TEXT NOT NULL CHECK (status IN ('confirmed', 'rejected', 'detected')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_result ON events (result);
CREATE INDEX IF NOT EXISTS idx_events_device_id ON events (device_id);

-- Seed default device
INSERT INTO devices (id, name, status, firmware, connection, microphone, sampling_rate, model, model_input)
VALUES ('ZYLOSE-ESP32-01', 'ZYLOSE-ESP32-01', 'offline', 'v1.0.0', 'Wi-Fi', 'INMP441', 16000, 'ZYLOSE INT8', '98 × 13')
ON CONFLICT (id) DO NOTHING;

UPDATE devices
SET status = 'offline', uptime = NULL, wifi_signal = NULL
WHERE id = 'ZYLOSE-ESP32-01' AND last_seen IS NULL;
