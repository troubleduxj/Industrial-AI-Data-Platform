from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DO $$
        BEGIN
            -- Add last_run_at
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='last_run_at') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "last_run_at" TIMESTAMPTZ;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."last_run_at" IS '最后执行时间';
                END IF;
            END IF;

            -- Add next_run_at
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='next_run_at') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "next_run_at" TIMESTAMPTZ;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."next_run_at" IS '下次执行时间';
                END IF;
            END IF;

            -- Add run_count
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='run_count') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "run_count" INT NOT NULL DEFAULT 0;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."run_count" IS '执行次数';
                END IF;
            END IF;

            -- Add success_count
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='success_count') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "success_count" INT NOT NULL DEFAULT 0;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."success_count" IS '成功次数';
                END IF;
            END IF;

            -- Add failure_count
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='failure_count') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "failure_count" INT NOT NULL DEFAULT 0;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."failure_count" IS '失败次数';
                END IF;
            END IF;
            
            -- Add schedule_config (just in case)
             IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='schedule_config') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "schedule_config" JSONB NOT NULL DEFAULT '{}';
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."schedule_config" IS '调度配置';
                END IF;
            END IF;
            
            -- Add schedule_type (just in case)
             IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='schedule_type') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "schedule_type" VARCHAR(20) NOT NULL DEFAULT 'cron';
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."schedule_type" IS '调度类型';
                END IF;
            END IF;
            
             -- Add is_active (just in case)
             IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='is_active') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "is_active" BOOL NOT NULL DEFAULT True;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."is_active" IS '是否启用';
                END IF;
            END IF;

        END
        $$;
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return ""
