-- Add is_alarm_enabled to t_device_field
ALTER TABLE t_device_field ADD COLUMN IF NOT EXISTS is_alarm_enabled BOOLEAN DEFAULT FALSE;

-- Add device_code and trigger_config to t_alarm_rule for Phase 2 support
ALTER TABLE t_alarm_rule ADD COLUMN IF NOT EXISTS device_code VARCHAR(64) NULL;
ALTER TABLE t_alarm_rule ADD COLUMN IF NOT EXISTS trigger_config JSONB NULL;

-- Create index for device_code
CREATE INDEX IF NOT EXISTS idx_alarm_rule_device ON t_alarm_rule (device_code);
