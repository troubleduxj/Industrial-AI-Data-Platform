-- 添加工作流卡片强调色字段
ALTER TABLE t_sys_workflow
ADD COLUMN IF NOT EXISTS accent_color VARCHAR(20) NULL;

COMMENT ON COLUMN t_sys_workflow.accent_color IS '卡片强调色(HEX)';
