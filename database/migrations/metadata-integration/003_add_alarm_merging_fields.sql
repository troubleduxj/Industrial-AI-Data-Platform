ALTER TABLE t_alarm_record ADD COLUMN last_triggered_at DATETIME NULL COMMENT '最近一次触发时间';
ALTER TABLE t_alarm_record ADD COLUMN trigger_count INT DEFAULT 1 COMMENT '触发次数';
