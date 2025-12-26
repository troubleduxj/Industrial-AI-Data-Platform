from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_t_sys_menu_order_b915d4";
        ALTER TABLE "t_sys_menu" ADD "perms" VARCHAR(100);
        ALTER TABLE "t_sys_menu" ADD "query" VARCHAR(255);
        ALTER TABLE "t_sys_menu" ADD "order_num" INT NOT NULL  DEFAULT 0;
        ALTER TABLE "t_sys_menu" ADD "status" BOOL NOT NULL  DEFAULT True;
        ALTER TABLE "t_sys_menu" ADD "visible" BOOL NOT NULL  DEFAULT True;
        ALTER TABLE "t_sys_menu" ADD "is_frame" BOOL NOT NULL  DEFAULT False;
        ALTER TABLE "t_sys_menu" ADD "is_cache" BOOL NOT NULL  DEFAULT True;
        ALTER TABLE "t_sys_menu" DROP COLUMN "keepalive";
        ALTER TABLE "t_sys_menu" DROP COLUMN "is_hidden";
        ALTER TABLE "t_sys_menu" DROP COLUMN "redirect";
        ALTER TABLE "t_sys_menu" DROP COLUMN "order";
        ALTER TABLE "t_sys_menu" ALTER COLUMN "parent_id" DROP DEFAULT;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "parent_id" DROP NOT NULL;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "parent_id" TYPE BIGINT USING "parent_id"::BIGINT;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "path" DROP NOT NULL;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "path" TYPE VARCHAR(200) USING "path"::VARCHAR(200);
        COMMENT ON COLUMN "t_sys_menu"."path" IS '路由路径';
        ALTER TABLE "t_sys_menu" ALTER COLUMN "component" DROP NOT NULL;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "component" TYPE VARCHAR(255) USING "component"::VARCHAR(255);
        COMMENT ON COLUMN "t_sys_menu"."component" IS '组件路径';
        ALTER TABLE "t_sys_api_groups" ALTER COLUMN "created_at" SET NOT NULL;
        ALTER TABLE "t_sys_api_groups" ALTER COLUMN "updated_at" SET NOT NULL;
        CREATE TABLE IF NOT EXISTS "t_device_field" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "device_type_code" VARCHAR(50) NOT NULL,
    "field_name" VARCHAR(100) NOT NULL,
    "field_code" VARCHAR(50) NOT NULL,
    "field_type" VARCHAR(20) NOT NULL,
    "field_category" VARCHAR(50) NOT NULL  DEFAULT 'data_collection',
    "unit" VARCHAR(20),
    "description" TEXT,
    "is_required" BOOL NOT NULL  DEFAULT False,
    "default_value" VARCHAR(255),
    "validation_rule" TEXT,
    "sort_order" INT NOT NULL  DEFAULT 0,
    "is_active" BOOL NOT NULL  DEFAULT True,
    CONSTRAINT "uid_t_device_fi_device__c91c42" UNIQUE ("device_type_code", "field_name")
);
CREATE INDEX IF NOT EXISTS "idx_t_device_fi_device__a72b4e" ON "t_device_field" ("device_type_code");
CREATE INDEX IF NOT EXISTS "idx_t_device_fi_device__3ee3b3" ON "t_device_field" ("device_type_code", "sort_order");
CREATE INDEX IF NOT EXISTS "idx_t_device_fi_device__a18aa9" ON "t_device_field" ("device_type_code", "field_category");
COMMENT ON COLUMN "t_sys_menu"."perms" IS '权限标识';
COMMENT ON COLUMN "t_sys_menu"."query" IS '路由参数';
COMMENT ON COLUMN "t_sys_menu"."order_num" IS '显示顺序';
COMMENT ON COLUMN "t_sys_menu"."status" IS '菜单状态';
COMMENT ON COLUMN "t_sys_menu"."visible" IS '显示状态';
COMMENT ON COLUMN "t_sys_menu"."is_frame" IS '是否外链';
COMMENT ON COLUMN "t_sys_menu"."is_cache" IS '是否缓存';
COMMENT ON COLUMN "t_device_field"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_field"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_field"."device_type_code" IS '设备类型代码';
COMMENT ON COLUMN "t_device_field"."field_name" IS '字段名称';
COMMENT ON COLUMN "t_device_field"."field_code" IS '字段代码';
COMMENT ON COLUMN "t_device_field"."field_type" IS '字段类型';
COMMENT ON COLUMN "t_device_field"."field_category" IS '字段分类：data_collection/maintenance_record';
COMMENT ON COLUMN "t_device_field"."unit" IS '单位';
COMMENT ON COLUMN "t_device_field"."description" IS '字段描述';
COMMENT ON COLUMN "t_device_field"."is_required" IS '是否必填';
COMMENT ON COLUMN "t_device_field"."default_value" IS '默认值';
COMMENT ON COLUMN "t_device_field"."validation_rule" IS '验证规则';
COMMENT ON COLUMN "t_device_field"."sort_order" IS '排序顺序';
COMMENT ON COLUMN "t_device_field"."is_active" IS '是否激活';
COMMENT ON TABLE "t_device_field" IS '设备字段定义表';
        CREATE TABLE IF NOT EXISTS "t_device_history_data" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "voltage" DOUBLE PRECISION,
    "current" DOUBLE PRECISION,
    "power" DOUBLE PRECISION,
    "temperature" DOUBLE PRECISION,
    "pressure" DOUBLE PRECISION,
    "vibration" DOUBLE PRECISION,
    "status" VARCHAR(20) NOT NULL,
    "error_code" VARCHAR(50),
    "error_message" TEXT,
    "data_timestamp" TIMESTAMPTZ NOT NULL,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_hi_device__bd0d51" ON "t_device_history_data" ("device_id", "data_timestamp");
CREATE INDEX IF NOT EXISTS "idx_t_device_hi_status_5172fb" ON "t_device_history_data" ("status");
COMMENT ON COLUMN "t_device_history_data"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_history_data"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_history_data"."voltage" IS '电压值(V)';
COMMENT ON COLUMN "t_device_history_data"."current" IS '电流值(A)';
COMMENT ON COLUMN "t_device_history_data"."power" IS '功率值(W)';
COMMENT ON COLUMN "t_device_history_data"."temperature" IS '温度值(°C)';
COMMENT ON COLUMN "t_device_history_data"."pressure" IS '压力值(Pa)';
COMMENT ON COLUMN "t_device_history_data"."vibration" IS '振动值';
COMMENT ON COLUMN "t_device_history_data"."status" IS '设备状态';
COMMENT ON COLUMN "t_device_history_data"."error_code" IS '错误代码';
COMMENT ON COLUMN "t_device_history_data"."error_message" IS '错误信息';
COMMENT ON COLUMN "t_device_history_data"."data_timestamp" IS '数据时间戳';
COMMENT ON COLUMN "t_device_history_data"."device_id" IS '关联设备';
COMMENT ON TABLE "t_device_history_data" IS '设备历史数据表';
        CREATE TABLE IF NOT EXISTS "t_device_info" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "device_code" VARCHAR(50) NOT NULL UNIQUE,
    "device_name" VARCHAR(100) NOT NULL,
    "device_model" VARCHAR(50),
    "device_type" VARCHAR(50),
    "manufacturer" VARCHAR(100),
    "production_date" DATE,
    "install_date" DATE,
    "install_location" VARCHAR(255),
    "online_address" VARCHAR(255),
    "team_name" VARCHAR(100),
    "is_locked" BOOL NOT NULL  DEFAULT False,
    "description" TEXT
);
CREATE INDEX IF NOT EXISTS "idx_t_device_in_device__a57ffb" ON "t_device_info" ("device_code");
CREATE INDEX IF NOT EXISTS "idx_t_device_in_device__6f5871" ON "t_device_info" ("device_name");
CREATE INDEX IF NOT EXISTS "idx_t_device_in_device__20f72f" ON "t_device_info" ("device_type");
CREATE INDEX IF NOT EXISTS "idx_t_device_in_manufac_6273a6" ON "t_device_info" ("manufacturer");
CREATE INDEX IF NOT EXISTS "idx_t_device_in_install_0fbf11" ON "t_device_info" ("install_location");
COMMENT ON COLUMN "t_device_info"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_info"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_info"."device_code" IS '设备编号，唯一标识';
COMMENT ON COLUMN "t_device_info"."device_name" IS '设备名称';
COMMENT ON COLUMN "t_device_info"."device_model" IS '设备型号';
COMMENT ON COLUMN "t_device_info"."device_type" IS '设备类型';
COMMENT ON COLUMN "t_device_info"."manufacturer" IS '制造商';
COMMENT ON COLUMN "t_device_info"."production_date" IS '出厂日期';
COMMENT ON COLUMN "t_device_info"."install_date" IS '安装日期';
COMMENT ON COLUMN "t_device_info"."install_location" IS '安装位置';
COMMENT ON COLUMN "t_device_info"."online_address" IS '设备在线地址';
COMMENT ON COLUMN "t_device_info"."team_name" IS '所属班组';
COMMENT ON COLUMN "t_device_info"."is_locked" IS '是否锁定状态';
COMMENT ON COLUMN "t_device_info"."description" IS '备注信息';
COMMENT ON TABLE "t_device_info" IS '设备基础信息表';
        CREATE TABLE IF NOT EXISTS "t_device_maintenance_plan" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "plan_name" VARCHAR(200) NOT NULL,
    "plan_description" TEXT,
    "maintenance_type" VARCHAR(50) NOT NULL,
    "frequency_type" VARCHAR(20) NOT NULL,
    "frequency_value" INT NOT NULL,
    "frequency_unit" VARCHAR(20),
    "start_date" DATE NOT NULL,
    "end_date" DATE,
    "last_execution_date" DATE,
    "next_execution_date" DATE NOT NULL,
    "estimated_duration" INT,
    "assigned_team" VARCHAR(100),
    "is_active" BOOL NOT NULL  DEFAULT True,
    "maintenance_checklist" TEXT,
    "required_tools" TEXT,
    "required_parts" TEXT,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_device__3c3680" ON "t_device_maintenance_plan" ("device_id", "next_execution_date");
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_is_acti_f5bdaa" ON "t_device_maintenance_plan" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_mainten_b779e2" ON "t_device_maintenance_plan" ("maintenance_type");
COMMENT ON COLUMN "t_device_maintenance_plan"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_maintenance_plan"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_maintenance_plan"."plan_name" IS '计划名称';
COMMENT ON COLUMN "t_device_maintenance_plan"."plan_description" IS '计划描述';
COMMENT ON COLUMN "t_device_maintenance_plan"."maintenance_type" IS '维护类型: preventive/inspection';
COMMENT ON COLUMN "t_device_maintenance_plan"."frequency_type" IS '频率类型: daily/weekly/monthly/quarterly/yearly/custom';
COMMENT ON COLUMN "t_device_maintenance_plan"."frequency_value" IS '频率值';
COMMENT ON COLUMN "t_device_maintenance_plan"."frequency_unit" IS '频率单位: days/weeks/months/years';
COMMENT ON COLUMN "t_device_maintenance_plan"."start_date" IS '开始日期';
COMMENT ON COLUMN "t_device_maintenance_plan"."end_date" IS '结束日期';
COMMENT ON COLUMN "t_device_maintenance_plan"."last_execution_date" IS '上次执行日期';
COMMENT ON COLUMN "t_device_maintenance_plan"."next_execution_date" IS '下次执行日期';
COMMENT ON COLUMN "t_device_maintenance_plan"."estimated_duration" IS '预估持续时间（分钟）';
COMMENT ON COLUMN "t_device_maintenance_plan"."assigned_team" IS '指定团队';
COMMENT ON COLUMN "t_device_maintenance_plan"."is_active" IS '是否激活';
COMMENT ON COLUMN "t_device_maintenance_plan"."maintenance_checklist" IS '维护检查清单，JSON格式';
COMMENT ON COLUMN "t_device_maintenance_plan"."required_tools" IS '所需工具，JSON格式';
COMMENT ON COLUMN "t_device_maintenance_plan"."required_parts" IS '所需零件，JSON格式';
COMMENT ON COLUMN "t_device_maintenance_plan"."device_id" IS '关联设备';
COMMENT ON TABLE "t_device_maintenance_plan" IS '设备维护计划表';
        CREATE TABLE IF NOT EXISTS "t_device_maintenance_record" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "maintenance_type" VARCHAR(50) NOT NULL,
    "maintenance_title" VARCHAR(200) NOT NULL,
    "maintenance_description" TEXT,
    "maintenance_status" VARCHAR(20) NOT NULL  DEFAULT 'planned',
    "priority" VARCHAR(20) NOT NULL  DEFAULT 'medium',
    "planned_start_time" TIMESTAMPTZ NOT NULL,
    "planned_end_time" TIMESTAMPTZ NOT NULL,
    "actual_start_time" TIMESTAMPTZ,
    "actual_end_time" TIMESTAMPTZ,
    "assigned_to" VARCHAR(100),
    "maintenance_team" VARCHAR(100),
    "estimated_cost" DECIMAL(10,2),
    "actual_cost" DECIMAL(10,2),
    "maintenance_result" TEXT,
    "parts_replaced" TEXT,
    "next_maintenance_date" TIMESTAMPTZ,
    "attachments" TEXT,
    "notes" TEXT,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_device__0b559a" ON "t_device_maintenance_record" ("device_id", "planned_start_time");
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_mainten_87d5e2" ON "t_device_maintenance_record" ("maintenance_status");
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_mainten_2cec53" ON "t_device_maintenance_record" ("maintenance_type");
COMMENT ON COLUMN "t_device_maintenance_record"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_maintenance_record"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_maintenance_record"."maintenance_type" IS '维护类型: preventive/corrective/emergency/inspection';
COMMENT ON COLUMN "t_device_maintenance_record"."maintenance_title" IS '维护标题';
COMMENT ON COLUMN "t_device_maintenance_record"."maintenance_description" IS '维护描述';
COMMENT ON COLUMN "t_device_maintenance_record"."maintenance_status" IS '维护状态: planned/in_progress/completed/cancelled';
COMMENT ON COLUMN "t_device_maintenance_record"."priority" IS '优先级: low/medium/high/urgent';
COMMENT ON COLUMN "t_device_maintenance_record"."planned_start_time" IS '计划开始时间';
COMMENT ON COLUMN "t_device_maintenance_record"."planned_end_time" IS '计划结束时间';
COMMENT ON COLUMN "t_device_maintenance_record"."actual_start_time" IS '实际开始时间';
COMMENT ON COLUMN "t_device_maintenance_record"."actual_end_time" IS '实际结束时间';
COMMENT ON COLUMN "t_device_maintenance_record"."assigned_to" IS '负责人';
COMMENT ON COLUMN "t_device_maintenance_record"."maintenance_team" IS '维护团队';
COMMENT ON COLUMN "t_device_maintenance_record"."estimated_cost" IS '预估成本';
COMMENT ON COLUMN "t_device_maintenance_record"."actual_cost" IS '实际成本';
COMMENT ON COLUMN "t_device_maintenance_record"."maintenance_result" IS '维护结果';
COMMENT ON COLUMN "t_device_maintenance_record"."parts_replaced" IS '更换的零件';
COMMENT ON COLUMN "t_device_maintenance_record"."next_maintenance_date" IS '下次维护日期';
COMMENT ON COLUMN "t_device_maintenance_record"."attachments" IS '附件路径，JSON格式';
COMMENT ON COLUMN "t_device_maintenance_record"."notes" IS '备注信息';
COMMENT ON COLUMN "t_device_maintenance_record"."device_id" IS '关联设备';
COMMENT ON TABLE "t_device_maintenance_record" IS '设备维护记录表';
        CREATE TABLE IF NOT EXISTS "t_device_maintenance_reminder" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "reminder_type" VARCHAR(20) NOT NULL,
    "reminder_title" VARCHAR(200) NOT NULL,
    "reminder_message" TEXT NOT NULL,
    "reminder_time" TIMESTAMPTZ NOT NULL,
    "due_date" TIMESTAMPTZ NOT NULL,
    "is_sent" BOOL NOT NULL  DEFAULT False,
    "is_read" BOOL NOT NULL  DEFAULT False,
    "is_dismissed" BOOL NOT NULL  DEFAULT False,
    "recipient_users" TEXT,
    "recipient_teams" TEXT,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE,
    "maintenance_plan_id" BIGINT REFERENCES "t_device_maintenance_plan" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_device__ee4a6e" ON "t_device_maintenance_reminder" ("device_id", "reminder_time");
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_is_sent_13b573" ON "t_device_maintenance_reminder" ("is_sent");
CREATE INDEX IF NOT EXISTS "idx_t_device_ma_reminde_48a79b" ON "t_device_maintenance_reminder" ("reminder_type");
COMMENT ON COLUMN "t_device_maintenance_reminder"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_maintenance_reminder"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_maintenance_reminder"."reminder_type" IS '提醒类型: plan/overdue/urgent';
COMMENT ON COLUMN "t_device_maintenance_reminder"."reminder_title" IS '提醒标题';
COMMENT ON COLUMN "t_device_maintenance_reminder"."reminder_message" IS '提醒消息';
COMMENT ON COLUMN "t_device_maintenance_reminder"."reminder_time" IS '提醒时间';
COMMENT ON COLUMN "t_device_maintenance_reminder"."due_date" IS '到期时间';
COMMENT ON COLUMN "t_device_maintenance_reminder"."is_sent" IS '是否已发送';
COMMENT ON COLUMN "t_device_maintenance_reminder"."is_read" IS '是否已读';
COMMENT ON COLUMN "t_device_maintenance_reminder"."is_dismissed" IS '是否已忽略';
COMMENT ON COLUMN "t_device_maintenance_reminder"."recipient_users" IS '接收用户，JSON格式';
COMMENT ON COLUMN "t_device_maintenance_reminder"."recipient_teams" IS '接收团队，JSON格式';
COMMENT ON COLUMN "t_device_maintenance_reminder"."device_id" IS '关联设备';
COMMENT ON COLUMN "t_device_maintenance_reminder"."maintenance_plan_id" IS '关联维护计划';
COMMENT ON TABLE "t_device_maintenance_reminder" IS '设备维护提醒表';
        CREATE TABLE IF NOT EXISTS "t_device_process" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "process_name" VARCHAR(200) NOT NULL,
    "process_code" VARCHAR(50) NOT NULL UNIQUE,
    "process_version" VARCHAR(20) NOT NULL  DEFAULT '1.0',
    "process_description" TEXT,
    "process_status" VARCHAR(20) NOT NULL  DEFAULT 'draft',
    "process_type" VARCHAR(50) NOT NULL,
    "process_category" VARCHAR(50),
    "process_parameters" TEXT,
    "quality_standards" TEXT,
    "safety_requirements" TEXT,
    "estimated_duration" INT,
    "difficulty_level" VARCHAR(20) NOT NULL  DEFAULT 'medium',
    "required_skills" TEXT,
    "created_by" VARCHAR(100),
    "approved_by" VARCHAR(100),
    "assigned_team" VARCHAR(100),
    "parent_process_id" INT,
    "is_template" BOOL NOT NULL  DEFAULT False,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "approval_status" VARCHAR(20) NOT NULL  DEFAULT 'pending',
    "approval_date" TIMESTAMPTZ,
    "approval_notes" TEXT,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_process_9b9942" ON "t_device_process" ("process_code");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_device__70c2a6" ON "t_device_process" ("device_id", "process_status");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_process_477c8b" ON "t_device_process" ("process_type");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_is_acti_0bada9" ON "t_device_process" ("is_active");
COMMENT ON COLUMN "t_device_process"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_process"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_process"."process_name" IS '工艺名称';
COMMENT ON COLUMN "t_device_process"."process_code" IS '工艺编码';
COMMENT ON COLUMN "t_device_process"."process_version" IS '工艺版本';
COMMENT ON COLUMN "t_device_process"."process_description" IS '工艺描述';
COMMENT ON COLUMN "t_device_process"."process_status" IS '工艺状态: draft/active/inactive/archived';
COMMENT ON COLUMN "t_device_process"."process_type" IS '工艺类型: welding/cutting/assembly/inspection';
COMMENT ON COLUMN "t_device_process"."process_category" IS '工艺分类';
COMMENT ON COLUMN "t_device_process"."process_parameters" IS '工艺参数，JSON格式';
COMMENT ON COLUMN "t_device_process"."quality_standards" IS '质量标准，JSON格式';
COMMENT ON COLUMN "t_device_process"."safety_requirements" IS '安全要求，JSON格式';
COMMENT ON COLUMN "t_device_process"."estimated_duration" IS '预估执行时间（分钟）';
COMMENT ON COLUMN "t_device_process"."difficulty_level" IS '难度等级: easy/medium/hard/expert';
COMMENT ON COLUMN "t_device_process"."required_skills" IS '所需技能，JSON格式';
COMMENT ON COLUMN "t_device_process"."created_by" IS '创建人';
COMMENT ON COLUMN "t_device_process"."approved_by" IS '审批人';
COMMENT ON COLUMN "t_device_process"."assigned_team" IS '指定团队';
COMMENT ON COLUMN "t_device_process"."parent_process_id" IS '父工艺ID（用于版本控制）';
COMMENT ON COLUMN "t_device_process"."is_template" IS '是否为模板';
COMMENT ON COLUMN "t_device_process"."is_active" IS '是否激活';
COMMENT ON COLUMN "t_device_process"."approval_status" IS '审批状态: pending/approved/rejected';
COMMENT ON COLUMN "t_device_process"."approval_date" IS '审批日期';
COMMENT ON COLUMN "t_device_process"."approval_notes" IS '审批备注';
COMMENT ON COLUMN "t_device_process"."device_id" IS '关联设备';
COMMENT ON TABLE "t_device_process" IS '设备工艺表';
        CREATE TABLE IF NOT EXISTS "t_device_process_execution" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "execution_code" VARCHAR(50) NOT NULL UNIQUE,
    "execution_name" VARCHAR(200) NOT NULL,
    "execution_description" TEXT,
    "execution_status" VARCHAR(20) NOT NULL  DEFAULT 'planned',
    "planned_start_time" TIMESTAMPTZ,
    "planned_end_time" TIMESTAMPTZ,
    "actual_start_time" TIMESTAMPTZ,
    "actual_end_time" TIMESTAMPTZ,
    "operator" VARCHAR(100),
    "supervisor" VARCHAR(100),
    "execution_team" VARCHAR(100),
    "execution_result" TEXT,
    "quality_result" VARCHAR(20),
    "quality_score" DOUBLE PRECISION,
    "quality_notes" TEXT,
    "issues_encountered" TEXT,
    "solutions_applied" TEXT,
    "materials_used" TEXT,
    "tools_used" TEXT,
    "energy_consumption" DOUBLE PRECISION,
    "estimated_cost" DOUBLE PRECISION,
    "actual_cost" DOUBLE PRECISION,
    "notes" TEXT,
    "attachments" TEXT,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE,
    "process_id" BIGINT NOT NULL REFERENCES "t_device_process" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_executi_0aa2b4" ON "t_device_process_execution" ("execution_code");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_device__f64647" ON "t_device_process_execution" ("device_id", "execution_status");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_process_ee552d" ON "t_device_process_execution" ("process_id", "execution_status");
COMMENT ON COLUMN "t_device_process_execution"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_process_execution"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_process_execution"."execution_code" IS '执行编号';
COMMENT ON COLUMN "t_device_process_execution"."execution_name" IS '执行名称';
COMMENT ON COLUMN "t_device_process_execution"."execution_description" IS '执行描述';
COMMENT ON COLUMN "t_device_process_execution"."execution_status" IS '执行状态: planned/in_progress/paused/completed/failed/cancelled';
COMMENT ON COLUMN "t_device_process_execution"."planned_start_time" IS '计划开始时间';
COMMENT ON COLUMN "t_device_process_execution"."planned_end_time" IS '计划结束时间';
COMMENT ON COLUMN "t_device_process_execution"."actual_start_time" IS '实际开始时间';
COMMENT ON COLUMN "t_device_process_execution"."actual_end_time" IS '实际结束时间';
COMMENT ON COLUMN "t_device_process_execution"."operator" IS '操作员';
COMMENT ON COLUMN "t_device_process_execution"."supervisor" IS '监督员';
COMMENT ON COLUMN "t_device_process_execution"."execution_team" IS '执行团队';
COMMENT ON COLUMN "t_device_process_execution"."execution_result" IS '执行结果';
COMMENT ON COLUMN "t_device_process_execution"."quality_result" IS '质量结果: pass/fail/pending';
COMMENT ON COLUMN "t_device_process_execution"."quality_score" IS '质量评分';
COMMENT ON COLUMN "t_device_process_execution"."quality_notes" IS '质量备注';
COMMENT ON COLUMN "t_device_process_execution"."issues_encountered" IS '遇到的问题，JSON格式';
COMMENT ON COLUMN "t_device_process_execution"."solutions_applied" IS '应用的解决方案，JSON格式';
COMMENT ON COLUMN "t_device_process_execution"."materials_used" IS '使用的材料，JSON格式';
COMMENT ON COLUMN "t_device_process_execution"."tools_used" IS '使用的工具，JSON格式';
COMMENT ON COLUMN "t_device_process_execution"."energy_consumption" IS '能耗';
COMMENT ON COLUMN "t_device_process_execution"."estimated_cost" IS '预估成本';
COMMENT ON COLUMN "t_device_process_execution"."actual_cost" IS '实际成本';
COMMENT ON COLUMN "t_device_process_execution"."notes" IS '备注信息';
COMMENT ON COLUMN "t_device_process_execution"."attachments" IS '附件信息，JSON格式';
COMMENT ON COLUMN "t_device_process_execution"."device_id" IS '关联设备';
COMMENT ON COLUMN "t_device_process_execution"."process_id" IS '关联工艺';
COMMENT ON TABLE "t_device_process_execution" IS '设备工艺执行记录表';
        CREATE TABLE IF NOT EXISTS "t_device_process_monitoring" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "monitoring_time" TIMESTAMPTZ NOT NULL,
    "process_parameters" TEXT,
    "parameter_status" VARCHAR(20) NOT NULL  DEFAULT 'normal',
    "quality_metrics" TEXT,
    "quality_status" VARCHAR(20) NOT NULL  DEFAULT 'normal',
    "device_status" VARCHAR(20) NOT NULL,
    "device_parameters" TEXT,
    "environmental_data" TEXT,
    "alarms" TEXT,
    "warnings" TEXT,
    "operator_notes" TEXT,
    "operator_rating" INT,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE,
    "execution_id" BIGINT NOT NULL REFERENCES "t_device_process_execution" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_executi_5c112c" ON "t_device_process_monitoring" ("execution_id", "monitoring_time");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_device__6f532e" ON "t_device_process_monitoring" ("device_id", "monitoring_time");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_paramet_450ddf" ON "t_device_process_monitoring" ("parameter_status");
COMMENT ON COLUMN "t_device_process_monitoring"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_process_monitoring"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_process_monitoring"."monitoring_time" IS '监控时间';
COMMENT ON COLUMN "t_device_process_monitoring"."process_parameters" IS '工艺参数值，JSON格式';
COMMENT ON COLUMN "t_device_process_monitoring"."parameter_status" IS '参数状态: normal/warning/alarm';
COMMENT ON COLUMN "t_device_process_monitoring"."quality_metrics" IS '质量指标，JSON格式';
COMMENT ON COLUMN "t_device_process_monitoring"."quality_status" IS '质量状态: normal/warning/alarm';
COMMENT ON COLUMN "t_device_process_monitoring"."device_status" IS '设备状态';
COMMENT ON COLUMN "t_device_process_monitoring"."device_parameters" IS '设备参数，JSON格式';
COMMENT ON COLUMN "t_device_process_monitoring"."environmental_data" IS '环境数据，JSON格式';
COMMENT ON COLUMN "t_device_process_monitoring"."alarms" IS '报警信息，JSON格式';
COMMENT ON COLUMN "t_device_process_monitoring"."warnings" IS '警告信息，JSON格式';
COMMENT ON COLUMN "t_device_process_monitoring"."operator_notes" IS '操作员备注';
COMMENT ON COLUMN "t_device_process_monitoring"."operator_rating" IS '操作员评分（1-5）';
COMMENT ON COLUMN "t_device_process_monitoring"."device_id" IS '关联设备';
COMMENT ON COLUMN "t_device_process_monitoring"."execution_id" IS '关联执行记录';
COMMENT ON TABLE "t_device_process_monitoring" IS '设备工艺监控数据表';
        CREATE TABLE IF NOT EXISTS "t_device_process_template" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "template_name" VARCHAR(200) NOT NULL,
    "template_code" VARCHAR(50) NOT NULL UNIQUE,
    "template_description" TEXT,
    "template_category" VARCHAR(50) NOT NULL,
    "device_type" VARCHAR(50),
    "process_type" VARCHAR(50) NOT NULL,
    "template_content" TEXT NOT NULL,
    "default_parameters" TEXT,
    "parameter_constraints" TEXT,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_public" BOOL NOT NULL  DEFAULT False,
    "created_by" VARCHAR(100),
    "maintained_by" VARCHAR(100),
    "usage_count" INT NOT NULL  DEFAULT 0,
    "last_used_date" TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_templat_e4a913" ON "t_device_process_template" ("template_code");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_templat_213b19" ON "t_device_process_template" ("template_category");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_device__4a9f7e" ON "t_device_process_template" ("device_type");
CREATE INDEX IF NOT EXISTS "idx_t_device_pr_is_acti_3085d5" ON "t_device_process_template" ("is_active");
COMMENT ON COLUMN "t_device_process_template"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_process_template"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_process_template"."template_name" IS '模板名称';
COMMENT ON COLUMN "t_device_process_template"."template_code" IS '模板编码';
COMMENT ON COLUMN "t_device_process_template"."template_description" IS '模板描述';
COMMENT ON COLUMN "t_device_process_template"."template_category" IS '模板分类';
COMMENT ON COLUMN "t_device_process_template"."device_type" IS '适用设备类型';
COMMENT ON COLUMN "t_device_process_template"."process_type" IS '工艺类型';
COMMENT ON COLUMN "t_device_process_template"."template_content" IS '模板内容，JSON格式';
COMMENT ON COLUMN "t_device_process_template"."default_parameters" IS '默认参数，JSON格式';
COMMENT ON COLUMN "t_device_process_template"."parameter_constraints" IS '参数约束，JSON格式';
COMMENT ON COLUMN "t_device_process_template"."is_active" IS '是否激活';
COMMENT ON COLUMN "t_device_process_template"."is_public" IS '是否公开';
COMMENT ON COLUMN "t_device_process_template"."created_by" IS '创建人';
COMMENT ON COLUMN "t_device_process_template"."maintained_by" IS '维护人';
COMMENT ON COLUMN "t_device_process_template"."usage_count" IS '使用次数';
COMMENT ON COLUMN "t_device_process_template"."last_used_date" IS '最后使用日期';
COMMENT ON TABLE "t_device_process_template" IS '设备工艺模板表';
        CREATE TABLE IF NOT EXISTS "t_device_realtime_data" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "voltage" DOUBLE PRECISION,
    "current" DOUBLE PRECISION,
    "power" DOUBLE PRECISION,
    "temperature" DOUBLE PRECISION,
    "pressure" DOUBLE PRECISION,
    "vibration" DOUBLE PRECISION,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'offline',
    "error_code" VARCHAR(50),
    "error_message" TEXT,
    "data_timestamp" TIMESTAMPTZ NOT NULL,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_re_device__c56d7b" ON "t_device_realtime_data" ("device_id", "data_timestamp");
CREATE INDEX IF NOT EXISTS "idx_t_device_re_status_846239" ON "t_device_realtime_data" ("status");
COMMENT ON COLUMN "t_device_realtime_data"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_realtime_data"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_realtime_data"."voltage" IS '电压值(V)';
COMMENT ON COLUMN "t_device_realtime_data"."current" IS '电流值(A)';
COMMENT ON COLUMN "t_device_realtime_data"."power" IS '功率值(W)';
COMMENT ON COLUMN "t_device_realtime_data"."temperature" IS '温度值(°C)';
COMMENT ON COLUMN "t_device_realtime_data"."pressure" IS '压力值(Pa)';
COMMENT ON COLUMN "t_device_realtime_data"."vibration" IS '振动值';
COMMENT ON COLUMN "t_device_realtime_data"."status" IS '设备状态: online/offline/error/maintenance';
COMMENT ON COLUMN "t_device_realtime_data"."error_code" IS '错误代码';
COMMENT ON COLUMN "t_device_realtime_data"."error_message" IS '错误信息';
COMMENT ON COLUMN "t_device_realtime_data"."data_timestamp" IS '数据时间戳';
COMMENT ON COLUMN "t_device_realtime_data"."device_id" IS '关联设备';
COMMENT ON TABLE "t_device_realtime_data" IS '设备实时数据表';
        CREATE TABLE IF NOT EXISTS "t_device_repair_record" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "device_type" VARCHAR(50) NOT NULL,
    "repair_date" DATE NOT NULL,
    "repair_code" VARCHAR(50)  UNIQUE,
    "repair_status" VARCHAR(20) NOT NULL  DEFAULT 'pending',
    "priority" VARCHAR(20) NOT NULL  DEFAULT 'medium',
    "applicant" VARCHAR(100) NOT NULL,
    "applicant_phone" VARCHAR(20),
    "applicant_dept" VARCHAR(100),
    "applicant_workshop" VARCHAR(100),
    "construction_unit" VARCHAR(100),
    "is_fault" BOOL NOT NULL  DEFAULT True,
    "fault_reason" VARCHAR(100),
    "damage_category" VARCHAR(50),
    "fault_content" TEXT,
    "fault_location" VARCHAR(200),
    "repair_content" TEXT,
    "parts_name" VARCHAR(500),
    "repairer" VARCHAR(100),
    "repair_start_time" TIMESTAMPTZ,
    "repair_completion_date" DATE,
    "repair_cost" DECIMAL(10,2),
    "device_specific_data" JSONB,
    "remarks" TEXT,
    "attachments" JSONB,
    "created_by" BIGINT,
    "updated_by" BIGINT,
    "device_id" BIGINT NOT NULL REFERENCES "t_device_info" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_device_re_device__e4b358" ON "t_device_repair_record" ("device_type");
CREATE INDEX IF NOT EXISTS "idx_t_device_re_repair__ddf7ba" ON "t_device_repair_record" ("repair_date");
CREATE INDEX IF NOT EXISTS "idx_t_device_re_repair__0bf323" ON "t_device_repair_record" ("repair_status");
CREATE INDEX IF NOT EXISTS "idx_t_device_re_applica_db4848" ON "t_device_repair_record" ("applicant");
CREATE INDEX IF NOT EXISTS "idx_t_device_re_device__5a85d7" ON "t_device_repair_record" ("device_id", "repair_date");
COMMENT ON COLUMN "t_device_repair_record"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_repair_record"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_repair_record"."device_type" IS '设备类型';
COMMENT ON COLUMN "t_device_repair_record"."repair_date" IS '报修日期';
COMMENT ON COLUMN "t_device_repair_record"."repair_code" IS '维修单号';
COMMENT ON COLUMN "t_device_repair_record"."repair_status" IS '维修状态：pending/in_progress/completed/cancelled';
COMMENT ON COLUMN "t_device_repair_record"."priority" IS '优先级：low/medium/high/urgent';
COMMENT ON COLUMN "t_device_repair_record"."applicant" IS '申请人';
COMMENT ON COLUMN "t_device_repair_record"."applicant_phone" IS '申请人电话';
COMMENT ON COLUMN "t_device_repair_record"."applicant_dept" IS '申请部门';
COMMENT ON COLUMN "t_device_repair_record"."applicant_workshop" IS '申请车间';
COMMENT ON COLUMN "t_device_repair_record"."construction_unit" IS '施工单位';
COMMENT ON COLUMN "t_device_repair_record"."is_fault" IS '是否故障';
COMMENT ON COLUMN "t_device_repair_record"."fault_reason" IS '故障原因';
COMMENT ON COLUMN "t_device_repair_record"."damage_category" IS '损坏类别';
COMMENT ON COLUMN "t_device_repair_record"."fault_content" IS '故障内容描述';
COMMENT ON COLUMN "t_device_repair_record"."fault_location" IS '故障部位';
COMMENT ON COLUMN "t_device_repair_record"."repair_content" IS '维修内容';
COMMENT ON COLUMN "t_device_repair_record"."parts_name" IS '更换配件名称';
COMMENT ON COLUMN "t_device_repair_record"."repairer" IS '维修人员';
COMMENT ON COLUMN "t_device_repair_record"."repair_start_time" IS '维修开始时间';
COMMENT ON COLUMN "t_device_repair_record"."repair_completion_date" IS '维修完成日期';
COMMENT ON COLUMN "t_device_repair_record"."repair_cost" IS '维修成本';
COMMENT ON COLUMN "t_device_repair_record"."device_specific_data" IS '设备特定字段数据';
COMMENT ON COLUMN "t_device_repair_record"."remarks" IS '备注';
COMMENT ON COLUMN "t_device_repair_record"."attachments" IS '附件信息';
COMMENT ON COLUMN "t_device_repair_record"."created_by" IS '创建人ID';
COMMENT ON COLUMN "t_device_repair_record"."updated_by" IS '更新人ID';
COMMENT ON COLUMN "t_device_repair_record"."device_id" IS '关联设备';
COMMENT ON TABLE "t_device_repair_record" IS '设备维修记录表';
        CREATE TABLE IF NOT EXISTS "t_device_type" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "type_name" VARCHAR(100) NOT NULL,
    "type_code" VARCHAR(50) NOT NULL UNIQUE,
    "tdengine_stable_name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "device_count" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_t_device_ty_type_na_98f7ba" ON "t_device_type" ("type_name");
CREATE INDEX IF NOT EXISTS "idx_t_device_ty_type_co_0de835" ON "t_device_type" ("type_code");
CREATE INDEX IF NOT EXISTS "idx_t_device_ty_is_acti_bcef85" ON "t_device_type" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_t_device_ty_is_acti_951d49" ON "t_device_type" ("is_active", "type_name");
CREATE INDEX IF NOT EXISTS "idx_t_device_ty_is_acti_a63386" ON "t_device_type" ("is_active", "type_code");
COMMENT ON COLUMN "t_device_type"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_device_type"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_device_type"."type_name" IS '设备类型名称';
COMMENT ON COLUMN "t_device_type"."type_code" IS '设备类型代码';
COMMENT ON COLUMN "t_device_type"."tdengine_stable_name" IS 'TDengine超级表名';
COMMENT ON COLUMN "t_device_type"."description" IS '设备类型描述';
COMMENT ON COLUMN "t_device_type"."is_active" IS '是否激活';
COMMENT ON COLUMN "t_device_type"."device_count" IS '该类型下的设备数量';
COMMENT ON TABLE "t_device_type" IS '设备类型表';
        CREATE TABLE IF NOT EXISTS "t_welding_alarm_his" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "prod_code" VARCHAR(64) NOT NULL,
    "alarm_time" TIMESTAMPTZ NOT NULL,
    "alarm_end_time" TIMESTAMPTZ,
    "alarm_duration_sec" INT,
    "alarm_code" VARCHAR(16),
    "alarm_message" TEXT,
    "alarm_solution" TEXT
);
CREATE INDEX IF NOT EXISTS "idx_t_welding_a_prod_co_00ab39" ON "t_welding_alarm_his" ("prod_code");
CREATE INDEX IF NOT EXISTS "idx_t_welding_a_alarm_t_f566d6" ON "t_welding_alarm_his" ("alarm_time");
CREATE INDEX IF NOT EXISTS "idx_t_welding_a_prod_co_0086f1" ON "t_welding_alarm_his" ("prod_code", "alarm_time");
COMMENT ON COLUMN "t_welding_alarm_his"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_welding_alarm_his"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_welding_alarm_his"."prod_code" IS '设备制造编码';
COMMENT ON COLUMN "t_welding_alarm_his"."alarm_time" IS '报警时刻（开始时间）';
COMMENT ON COLUMN "t_welding_alarm_his"."alarm_end_time" IS '报警结束时刻';
COMMENT ON COLUMN "t_welding_alarm_his"."alarm_duration_sec" IS '报警持续秒数（可解析得出）';
COMMENT ON COLUMN "t_welding_alarm_his"."alarm_code" IS '报警代码';
COMMENT ON COLUMN "t_welding_alarm_his"."alarm_message" IS '报警内容';
COMMENT ON COLUMN "t_welding_alarm_his"."alarm_solution" IS '解决方法（目前为空，但字段预留）';
COMMENT ON TABLE "t_welding_alarm_his" IS '焊接报警历史表';
        DROP TABLE IF EXISTS "t_ai_health_scores";
        DROP TABLE IF EXISTS "api";
        DROP TABLE IF EXISTS "t_ai_analysis";
        DROP TABLE IF EXISTS "t_ai_annotation_projects";
        DROP TABLE IF EXISTS "t_ai_predictions";
        DROP TABLE IF EXISTS "t_ai_models";
        CREATE INDEX "idx_t_sys_menu_perms_d80270" ON "t_sys_menu" ("perms");
        CREATE INDEX "idx_t_sys_menu_order_n_eeae54" ON "t_sys_menu" ("order_num");
        CREATE INDEX "idx_t_sys_menu_status_8b0022" ON "t_sys_menu" ("status");
        CREATE INDEX "idx_t_sys_menu_visible_3f4f2d" ON "t_sys_menu" ("visible");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_t_sys_menu_visible_3f4f2d";
        DROP INDEX IF EXISTS "idx_t_sys_menu_status_8b0022";
        DROP INDEX IF EXISTS "idx_t_sys_menu_order_n_eeae54";
        DROP INDEX IF EXISTS "idx_t_sys_menu_perms_d80270";
        ALTER TABLE "t_sys_menu" ADD "keepalive" BOOL NOT NULL  DEFAULT True;
        ALTER TABLE "t_sys_menu" ADD "is_hidden" BOOL NOT NULL  DEFAULT False;
        ALTER TABLE "t_sys_menu" ADD "redirect" VARCHAR(100);
        ALTER TABLE "t_sys_menu" ADD "order" INT NOT NULL  DEFAULT 0;
        ALTER TABLE "t_sys_menu" DROP COLUMN "perms";
        ALTER TABLE "t_sys_menu" DROP COLUMN "query";
        ALTER TABLE "t_sys_menu" DROP COLUMN "order_num";
        ALTER TABLE "t_sys_menu" DROP COLUMN "status";
        ALTER TABLE "t_sys_menu" DROP COLUMN "visible";
        ALTER TABLE "t_sys_menu" DROP COLUMN "is_frame";
        ALTER TABLE "t_sys_menu" DROP COLUMN "is_cache";
        ALTER TABLE "t_sys_menu" ALTER COLUMN "parent_id" TYPE INT USING "parent_id"::INT;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "parent_id" SET NOT NULL;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "parent_id" SET DEFAULT 0;
        ALTER TABLE "t_sys_menu" ALTER COLUMN "path" SET NOT NULL;
        COMMENT ON COLUMN "t_sys_menu"."path" IS '菜单路径';
        ALTER TABLE "t_sys_menu" ALTER COLUMN "path" TYPE VARCHAR(100) USING "path"::VARCHAR(100);
        ALTER TABLE "t_sys_menu" ALTER COLUMN "component" SET NOT NULL;
        COMMENT ON COLUMN "t_sys_menu"."component" IS '组件';
        ALTER TABLE "t_sys_menu" ALTER COLUMN "component" TYPE VARCHAR(100) USING "component"::VARCHAR(100);
        ALTER TABLE "t_sys_api_groups" ALTER COLUMN "created_at" DROP NOT NULL;
        ALTER TABLE "t_sys_api_groups" ALTER COLUMN "updated_at" DROP NOT NULL;
        DROP TABLE IF EXISTS "t_device_maintenance_record";
        DROP TABLE IF EXISTS "t_device_info";
        DROP TABLE IF EXISTS "t_device_process";
        DROP TABLE IF EXISTS "t_device_maintenance_plan";
        DROP TABLE IF EXISTS "t_device_history_data";
        DROP TABLE IF EXISTS "t_device_process_monitoring";
        DROP TABLE IF EXISTS "t_device_process_template";
        DROP TABLE IF EXISTS "t_welding_alarm_his";
        DROP TABLE IF EXISTS "t_device_realtime_data";
        DROP TABLE IF EXISTS "t_device_process_execution";
        DROP TABLE IF EXISTS "t_device_field";
        DROP TABLE IF EXISTS "t_device_repair_record";
        DROP TABLE IF EXISTS "t_device_maintenance_reminder";
        DROP TABLE IF EXISTS "t_device_type";
        CREATE INDEX "idx_t_sys_menu_order_b915d4" ON "t_sys_menu" ("order");"""
