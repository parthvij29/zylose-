# Zylose Dashboard

Next.js dashboard for displaying Zylose edge-model events stored in Supabase.
The dashboard reads event, device, and analytics data from the database; it does
not generate sample detections. If Supabase is not configured, the API returns
a configuration error rather than showing dummy figures.

## Connect Supabase

1. Create a Supabase project.
2. In the Supabase project, open **SQL Editor** and run [`supabase/schema.sql`](./supabase/schema.sql). It creates the `devices` and `events` tables and registers the initial Zylose device as offline.
3. In Supabase **Project Settings → API**, copy the Project URL and `service_role` key.
4. Copy `.env.local.example` to `.env.local` in this project directory and fill in the values:

   ```env
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```

   Keep the service-role key private. Do not add a `NEXT_PUBLIC_` prefix, put it
   in client-side code, commit `.env.local`, or share it in chat.
5. Restart the Next.js dev server after saving `.env.local`:

   ```powershell
   npm run dev
   ```

The dashboard API routes use these server-only credentials. The Overview,
Activity, Analytics, and Devices pages will show an error until the database is
configured. Once configured, empty tables show zero counts and no events.

## Send real inference events

The inference device or its companion program must send each model result to
`POST /api/events`. The endpoint saves the event to Supabase; the dashboard
polls the database-backed API and updates automatically. The seeded device ID
is `ZYLOSE-ESP32-01`. Example request body (scores are probabilities from `0`
to `1`):

```json
{
  "device_id": "ZYLOSE-ESP32-01",
  "result": "zylose",
  "confidence": 0.91,
  "unknown_score": 0.06,
  "silence_score": 0.03
}
```

For a device on the same local network, send the request to
`http://<computer-lan-ip>:3000/api/events` rather than `localhost`; from a
deployed device use the deployed dashboard URL. The computer/server must be
reachable by the device. Use the response status to detect a failed database
write; a `201` response means the event was saved.

[`../Voice-activator-tinyml/scripts/preprocess.py`](../Voice-activator-tinyml/scripts/preprocess.py)
prepares training audio; it does not send inference results to the dashboard.
To see real-time data, the firmware/inference process must make the POST
request after it classifies an audio sample.

## What the displayed metrics mean

- Detection counts, distribution, and hourly activity are calculated from
  rows in `events`.
- Confidence values are model output probabilities saved with each event.
  Confidence is not the same as validated accuracy.
- Precision and recall need ground-truth labels for predictions, which the
  current event schema does not store, so the dashboard does not invent them.
- Device CPU and memory are not collected by the current event API. Uptime and
  Wi-Fi signal show “Not reported” unless the database has those values.
