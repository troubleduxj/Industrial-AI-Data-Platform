from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DO $$
        BEGIN
            -- Add metrics column
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_device_realtime_data') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='t_device_realtime_data' AND column_name='metrics') THEN
                    ALTER TABLE "t_device_realtime_data" ADD COLUMN "metrics" JSONB;
                    COMMENT ON COLUMN "t_device_realtime_data"."metrics" IS '实时指标快照';
                END IF;
            END IF;

            -- Drop old columns to match model definition
            ALTER TABLE "t_device_realtime_data" DROP COLUMN IF EXISTS "voltage";
            ALTER TABLE "t_device_realtime_data" DROP COLUMN IF EXISTS "current";
            ALTER TABLE "t_device_realtime_data" DROP COLUMN IF EXISTS "power";
            ALTER TABLE "t_device_realtime_data" DROP COLUMN IF EXISTS "temperature";
            ALTER TABLE "t_device_realtime_data" DROP COLUMN IF EXISTS "pressure";
            ALTER TABLE "t_device_realtime_data" DROP COLUMN IF EXISTS "vibration";
            
        END
        $$;
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return ""
