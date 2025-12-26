from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DO $$
        BEGIN
            -- Add start_time
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='start_time') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "start_time" TIMESTAMPTZ;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."start_time" IS '开始时间';
                END IF;
            END IF;

            -- Add end_time
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='end_time') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "end_time" TIMESTAMPTZ;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."end_time" IS '结束时间';
                END IF;
            END IF;

            -- Add created_by
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='created_by') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "created_by" BIGINT;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."created_by" IS '创建人ID';
                END IF;
            END IF;

            -- Add created_by_name
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='created_by_name') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "created_by_name" VARCHAR(50);
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."created_by_name" IS '创建人姓名';
                END IF;
            END IF;

            -- Add created_at (TimestampMixin)
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='created_at') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."created_at" IS '创建时间';
                END IF;
            END IF;

            -- Add updated_at (TimestampMixin)
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='updated_at') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."updated_at" IS '更新时间';
                END IF;
            END IF;

        END
        $$;
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return ""
