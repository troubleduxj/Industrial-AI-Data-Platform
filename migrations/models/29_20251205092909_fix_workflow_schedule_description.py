from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DO $$
        BEGIN
            -- 1. Ensure t_sys_workflow exists (basic check, assuming it exists or created elsewhere)
            -- If it doesn't exist, this migration might fail on FK if creating schedule table. 
            -- But we assume main workflow table exists as user only reported schedule field error.

            -- 2. Create t_sys_workflow_schedule if not exists
            CREATE TABLE IF NOT EXISTS "t_sys_workflow_schedule" (
                "created_at" TIMESTAMPTZ NOT NULL,
                "updated_at" TIMESTAMPTZ NOT NULL,
                "id" BIGSERIAL NOT NULL PRIMARY KEY,
                "name" VARCHAR(100),
                "description" TEXT,
                "schedule_type" VARCHAR(20) NOT NULL,
                "schedule_config" JSONB NOT NULL,
                "start_time" TIMESTAMPTZ,
                "end_time" TIMESTAMPTZ,
                "is_active" BOOL NOT NULL  DEFAULT True,
                "run_count" INT NOT NULL  DEFAULT 0,
                "success_count" INT NOT NULL  DEFAULT 0,
                "failure_count" INT NOT NULL  DEFAULT 0,
                "last_run_at" TIMESTAMPTZ,
                "next_run_at" TIMESTAMPTZ,
                "created_by" BIGINT,
                "created_by_name" VARCHAR(50),
                "workflow_id" BIGINT NOT NULL REFERENCES "t_sys_workflow" ("id") ON DELETE CASCADE
            );

            -- 3. Add description column if table exists but column is missing
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='description') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "description" TEXT;
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."description" IS '调度描述';
                END IF;
            END IF;
            
            -- 4. Add other columns that might be missing based on model definition (just in case)
             IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_sys_workflow_schedule') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_sys_workflow_schedule' AND column_name='name') THEN
                    ALTER TABLE "t_sys_workflow_schedule" ADD COLUMN "name" VARCHAR(100);
                    COMMENT ON COLUMN "t_sys_workflow_schedule"."name" IS '调度名称';
                END IF;
            END IF;

        END
        $$;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Downgrade logic if needed, but for drift fix, usually empty or specific rollback
    """
