-- Phase 1 Schema Refactoring for Universal Device Adaptation

-- 1. Add attributes to t_device_info
ALTER TABLE "t_device_info" ADD COLUMN IF NOT EXISTS "attributes" JSONB;

-- 2. Add metrics to t_device_realtime_data
ALTER TABLE "t_device_realtime_data" ADD COLUMN IF NOT EXISTS "metrics" JSONB;

-- 3. Create t_device_alarm_history table
CREATE TABLE IF NOT EXISTS "t_device_alarm_history" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "alarm_code" VARCHAR(50) NOT NULL,
    "severity" VARCHAR(20) NOT NULL  DEFAULT 'Error',
    "category" VARCHAR(50) NOT NULL  DEFAULT 'Device',
    "content" TEXT NOT NULL,
    "start_time" TIMESTAMPTZ NOT NULL,
    "end_time" TIMESTAMPTZ,
    "context" JSONB,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "idx_t_device_al_device__232692" ON "t_device_alarm_history" ("device_id", "start_time");
CREATE INDEX IF NOT EXISTS "idx_t_device_al_severit_3c6805" ON "t_device_alarm_history" ("severity");
CREATE INDEX IF NOT EXISTS "idx_t_device_al_alarm_c_640688" ON "t_device_alarm_history" ("alarm_code");

-- Note: Data migration logic is handled by python script database/migrations/migrate_alarms.py
