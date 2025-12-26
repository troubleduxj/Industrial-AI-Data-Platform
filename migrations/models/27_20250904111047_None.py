from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "api" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "path" VARCHAR(100) NOT NULL,
    "method" VARCHAR(6) NOT NULL,
    "summary" VARCHAR(500),
    "description" TEXT,
    "tags" VARCHAR(100),
    "is_active" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_api_path_9ed611" ON "api" ("path");
CREATE INDEX IF NOT EXISTS "idx_api_method_a46dfb" ON "api" ("method");
CREATE INDEX IF NOT EXISTS "idx_api_summary_400f73" ON "api" ("summary");
CREATE INDEX IF NOT EXISTS "idx_api_tags_04ae27" ON "api" ("tags");
CREATE INDEX IF NOT EXISTS "idx_api_is_acti_4efa3a" ON "api" ("is_active");
COMMENT ON COLUMN "api"."created_at" IS '创建时间';
COMMENT ON COLUMN "api"."updated_at" IS '更新时间';
COMMENT ON COLUMN "api"."path" IS 'API路径';
COMMENT ON COLUMN "api"."method" IS '请求方法';
COMMENT ON COLUMN "api"."summary" IS '请求简介';
COMMENT ON COLUMN "api"."description" IS 'API详细描述';
COMMENT ON COLUMN "api"."tags" IS 'API标签';
COMMENT ON COLUMN "api"."is_active" IS '是否启用';
CREATE TABLE IF NOT EXISTS "t_sys_auditlog" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "user_id" INT NOT NULL,
    "username" VARCHAR(64) NOT NULL  DEFAULT '',
    "module" VARCHAR(64) NOT NULL  DEFAULT '',
    "summary" VARCHAR(128) NOT NULL  DEFAULT '',
    "method" VARCHAR(10) NOT NULL  DEFAULT '',
    "path" VARCHAR(255) NOT NULL  DEFAULT '',
    "status" INT NOT NULL  DEFAULT -1,
    "response_time" INT NOT NULL  DEFAULT 0,
    "request_args" JSONB,
    "response_body" JSONB
);
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_user_id_b2ad1a" ON "t_sys_auditlog" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_usernam_cdff49" ON "t_sys_auditlog" ("username");
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_module_a2f8d8" ON "t_sys_auditlog" ("module");
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_summary_9b7ed8" ON "t_sys_auditlog" ("summary");
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_method_255ba3" ON "t_sys_auditlog" ("method");
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_path_d60e3e" ON "t_sys_auditlog" ("path");
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_status_6180f7" ON "t_sys_auditlog" ("status");
CREATE INDEX IF NOT EXISTS "idx_t_sys_audit_respons_7892d8" ON "t_sys_auditlog" ("response_time");
COMMENT ON COLUMN "t_sys_auditlog"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_auditlog"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_auditlog"."user_id" IS '用户ID';
COMMENT ON COLUMN "t_sys_auditlog"."username" IS '用户名称';
COMMENT ON COLUMN "t_sys_auditlog"."module" IS '功能模块';
COMMENT ON COLUMN "t_sys_auditlog"."summary" IS '请求描述';
COMMENT ON COLUMN "t_sys_auditlog"."method" IS '请求方法';
COMMENT ON COLUMN "t_sys_auditlog"."path" IS '请求路径';
COMMENT ON COLUMN "t_sys_auditlog"."status" IS '状态码';
COMMENT ON COLUMN "t_sys_auditlog"."response_time" IS '响应时间(单位ms)';
COMMENT ON COLUMN "t_sys_auditlog"."request_args" IS '请求参数';
COMMENT ON COLUMN "t_sys_auditlog"."response_body" IS '返回数据';
CREATE TABLE IF NOT EXISTS "t_sys_dept" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "dept_name" VARCHAR(50) NOT NULL  DEFAULT '',
    "ancestors" VARCHAR(500),
    "order_num" INT NOT NULL  DEFAULT 0,
    "leader" VARCHAR(20),
    "phone" VARCHAR(11),
    "email" VARCHAR(50),
    "status" VARCHAR(1) NOT NULL  DEFAULT '0',
    "del_flag" VARCHAR(1) NOT NULL  DEFAULT '0',
    "parent_id" BIGINT
);
COMMENT ON COLUMN "t_sys_dept"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_dept"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_dept"."dept_name" IS '部门名称';
COMMENT ON COLUMN "t_sys_dept"."ancestors" IS '祖级列表';
COMMENT ON COLUMN "t_sys_dept"."order_num" IS '显示顺序';
COMMENT ON COLUMN "t_sys_dept"."leader" IS '负责人';
COMMENT ON COLUMN "t_sys_dept"."phone" IS '联系电话';
COMMENT ON COLUMN "t_sys_dept"."email" IS '邮箱';
COMMENT ON COLUMN "t_sys_dept"."status" IS '部门状态（0正常 1停用）';
COMMENT ON COLUMN "t_sys_dept"."del_flag" IS '删除标志（0代表存在 2代表删除）';
COMMENT ON COLUMN "t_sys_dept"."parent_id" IS '父部门ID';
CREATE TABLE IF NOT EXISTS "t_sys_dept_closure" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "level" INT NOT NULL  DEFAULT 0,
    "ancestor_id" BIGINT NOT NULL REFERENCES "t_sys_dept" ("id") ON DELETE CASCADE,
    "descendant_id" BIGINT NOT NULL REFERENCES "t_sys_dept" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_t_sys_dept__ancesto_9a8281" UNIQUE ("ancestor_id", "descendant_id")
);
COMMENT ON COLUMN "t_sys_dept_closure"."level" IS '深度';
COMMENT ON COLUMN "t_sys_dept_closure"."ancestor_id" IS '祖先ID';
COMMENT ON COLUMN "t_sys_dept_closure"."descendant_id" IS '后代ID';
CREATE TABLE IF NOT EXISTS "t_sys_menu" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(20) NOT NULL,
    "remark" JSONB,
    "menu_type" VARCHAR(7),
    "icon" VARCHAR(100),
    "path" VARCHAR(100) NOT NULL,
    "order" INT NOT NULL  DEFAULT 0,
    "parent_id" INT NOT NULL  DEFAULT 0,
    "is_hidden" BOOL NOT NULL  DEFAULT False,
    "component" VARCHAR(100) NOT NULL,
    "keepalive" BOOL NOT NULL  DEFAULT True,
    "redirect" VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS "idx_t_sys_menu_name_88073e" ON "t_sys_menu" ("name");
CREATE INDEX IF NOT EXISTS "idx_t_sys_menu_path_d8a60c" ON "t_sys_menu" ("path");
CREATE INDEX IF NOT EXISTS "idx_t_sys_menu_order_b915d4" ON "t_sys_menu" ("order");
CREATE INDEX IF NOT EXISTS "idx_t_sys_menu_parent__1a9c8a" ON "t_sys_menu" ("parent_id");
COMMENT ON COLUMN "t_sys_menu"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_menu"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_menu"."name" IS '菜单名称';
COMMENT ON COLUMN "t_sys_menu"."remark" IS '保留字段';
COMMENT ON COLUMN "t_sys_menu"."menu_type" IS '菜单类型';
COMMENT ON COLUMN "t_sys_menu"."icon" IS '菜单图标';
COMMENT ON COLUMN "t_sys_menu"."path" IS '菜单路径';
COMMENT ON COLUMN "t_sys_menu"."order" IS '排序';
COMMENT ON COLUMN "t_sys_menu"."parent_id" IS '父菜单ID';
COMMENT ON COLUMN "t_sys_menu"."is_hidden" IS '是否隐藏';
COMMENT ON COLUMN "t_sys_menu"."component" IS '组件';
COMMENT ON COLUMN "t_sys_menu"."keepalive" IS '存活';
COMMENT ON COLUMN "t_sys_menu"."redirect" IS '重定向';
CREATE TABLE IF NOT EXISTS "t_sys_role" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "role_name" VARCHAR(20) NOT NULL UNIQUE,
    "role_key" VARCHAR(100),
    "role_sort" INT,
    "data_scope" VARCHAR(20),
    "menu_check_strictly" BOOL NOT NULL  DEFAULT True,
    "dept_check_strictly" BOOL NOT NULL  DEFAULT True,
    "status" VARCHAR(20) NOT NULL  DEFAULT '0',
    "del_flag" VARCHAR(10) NOT NULL  DEFAULT '0',
    "remark" TEXT,
    "parent_id" BIGINT
);
CREATE INDEX IF NOT EXISTS "idx_t_sys_role_role_na_74d2aa" ON "t_sys_role" ("role_name");
CREATE INDEX IF NOT EXISTS "idx_t_sys_role_role_ke_0647d9" ON "t_sys_role" ("role_key");
CREATE INDEX IF NOT EXISTS "idx_t_sys_role_role_so_57f824" ON "t_sys_role" ("role_sort");
CREATE INDEX IF NOT EXISTS "idx_t_sys_role_data_sc_9ac81f" ON "t_sys_role" ("data_scope");
CREATE INDEX IF NOT EXISTS "idx_t_sys_role_status_2a70c3" ON "t_sys_role" ("status");
CREATE INDEX IF NOT EXISTS "idx_t_sys_role_del_fla_210245" ON "t_sys_role" ("del_flag");
CREATE INDEX IF NOT EXISTS "idx_t_sys_role_parent__58366d" ON "t_sys_role" ("parent_id");
COMMENT ON COLUMN "t_sys_role"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_role"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_role"."role_name" IS '角色名称';
COMMENT ON COLUMN "t_sys_role"."role_key" IS '角色权限字符串';
COMMENT ON COLUMN "t_sys_role"."role_sort" IS '显示顺序';
COMMENT ON COLUMN "t_sys_role"."data_scope" IS '数据范围';
COMMENT ON COLUMN "t_sys_role"."menu_check_strictly" IS '菜单树选择项是否关联显示';
COMMENT ON COLUMN "t_sys_role"."dept_check_strictly" IS '部门树选择项是否关联显示';
COMMENT ON COLUMN "t_sys_role"."status" IS '角色状态';
COMMENT ON COLUMN "t_sys_role"."del_flag" IS '删除标志';
COMMENT ON COLUMN "t_sys_role"."remark" IS '备注';
COMMENT ON COLUMN "t_sys_role"."parent_id" IS '父角色ID';
CREATE TABLE IF NOT EXISTS "t_sys_api_groups" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "group_code" VARCHAR(100) NOT NULL UNIQUE,
    "group_name" VARCHAR(200) NOT NULL,
    "parent_id" BIGINT,
    "description" TEXT,
    "sort_order" INT,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'active',
    "created_at" TIMESTAMPTZ,
    "updated_at" TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_g_group_c_dc32fd" ON "t_sys_api_groups" ("group_code");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_g_parent__f3a835" ON "t_sys_api_groups" ("parent_id");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_g_status_39c9a9" ON "t_sys_api_groups" ("status");
COMMENT ON COLUMN "t_sys_api_groups"."group_code" IS '分组编码';
COMMENT ON COLUMN "t_sys_api_groups"."group_name" IS '分组名称';
COMMENT ON COLUMN "t_sys_api_groups"."parent_id" IS '父分组ID';
COMMENT ON COLUMN "t_sys_api_groups"."description" IS '描述';
COMMENT ON COLUMN "t_sys_api_groups"."sort_order" IS '排序';
COMMENT ON COLUMN "t_sys_api_groups"."status" IS '状态';
COMMENT ON COLUMN "t_sys_api_groups"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_api_groups"."updated_at" IS '更新时间';
COMMENT ON TABLE "t_sys_api_groups" IS '系统API分组模型 - 对应t_sys_api_groups表';
CREATE TABLE IF NOT EXISTS "t_sys_api_endpoints" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "api_code" VARCHAR(100) NOT NULL UNIQUE,
    "api_name" VARCHAR(200) NOT NULL,
    "api_path" VARCHAR(500) NOT NULL,
    "http_method" VARCHAR(10) NOT NULL,
    "description" TEXT,
    "version" VARCHAR(20) NOT NULL  DEFAULT 'v2',
    "is_public" BOOL NOT NULL  DEFAULT False,
    "is_deprecated" BOOL NOT NULL  DEFAULT False,
    "rate_limit" INT,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'active',
    "permission_code" VARCHAR(100),
    "created_at" TIMESTAMPTZ,
    "updated_at" TIMESTAMPTZ,
    "group_id" BIGINT REFERENCES "t_sys_api_groups" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_api_cod_aad034" ON "t_sys_api_endpoints" ("api_code");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_api_pat_ed27db" ON "t_sys_api_endpoints" ("api_path");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_http_me_e83905" ON "t_sys_api_endpoints" ("http_method");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_version_b363e7" ON "t_sys_api_endpoints" ("version");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_is_publ_0fd634" ON "t_sys_api_endpoints" ("is_public");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_is_depr_def1d7" ON "t_sys_api_endpoints" ("is_deprecated");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_status_c1f097" ON "t_sys_api_endpoints" ("status");
CREATE INDEX IF NOT EXISTS "idx_t_sys_api_e_permiss_e129e7" ON "t_sys_api_endpoints" ("permission_code");
COMMENT ON COLUMN "t_sys_api_endpoints"."api_code" IS 'API编码';
COMMENT ON COLUMN "t_sys_api_endpoints"."api_name" IS 'API名称';
COMMENT ON COLUMN "t_sys_api_endpoints"."api_path" IS 'API路径';
COMMENT ON COLUMN "t_sys_api_endpoints"."http_method" IS 'HTTP方法';
COMMENT ON COLUMN "t_sys_api_endpoints"."description" IS '描述';
COMMENT ON COLUMN "t_sys_api_endpoints"."version" IS '版本';
COMMENT ON COLUMN "t_sys_api_endpoints"."is_public" IS '是否公开';
COMMENT ON COLUMN "t_sys_api_endpoints"."is_deprecated" IS '是否废弃';
COMMENT ON COLUMN "t_sys_api_endpoints"."rate_limit" IS '速率限制';
COMMENT ON COLUMN "t_sys_api_endpoints"."status" IS '状态';
COMMENT ON COLUMN "t_sys_api_endpoints"."permission_code" IS '权限编码';
COMMENT ON COLUMN "t_sys_api_endpoints"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_api_endpoints"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_api_endpoints"."group_id" IS '所属分组';
COMMENT ON TABLE "t_sys_api_endpoints" IS '系统API端点模型 - 对应t_sys_api_endpoints表';
CREATE TABLE IF NOT EXISTS "t_sys_user" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(20) NOT NULL UNIQUE,
    "nick_name" VARCHAR(30),
    "user_type" VARCHAR(20),
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "phone_number" VARCHAR(20),
    "sex" VARCHAR(10),
    "avatar" VARCHAR(255),
    "password" VARCHAR(128),
    "status" VARCHAR(20) NOT NULL  DEFAULT '0',
    "del_flag" VARCHAR(10) NOT NULL  DEFAULT '0',
    "login_ip" VARCHAR(50),
    "login_date" TIMESTAMPTZ,
    "remark" TEXT,
    "dept_id" BIGINT REFERENCES "t_sys_dept" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_usernam_34c30f" ON "t_sys_user" ("username");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_nick_na_87b2f6" ON "t_sys_user" ("nick_name");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_user_ty_d6227c" ON "t_sys_user" ("user_type");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_email_e85072" ON "t_sys_user" ("email");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_phone_n_fbe99b" ON "t_sys_user" ("phone_number");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_sex_8459d7" ON "t_sys_user" ("sex");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_avatar_c6a9c8" ON "t_sys_user" ("avatar");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_status_d44c01" ON "t_sys_user" ("status");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_del_fla_56f984" ON "t_sys_user" ("del_flag");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_login_i_4c1365" ON "t_sys_user" ("login_ip");
CREATE INDEX IF NOT EXISTS "idx_t_sys_user_login_d_045482" ON "t_sys_user" ("login_date");
COMMENT ON COLUMN "t_sys_user"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_user"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_user"."username" IS '用户名称';
COMMENT ON COLUMN "t_sys_user"."nick_name" IS '昵称';
COMMENT ON COLUMN "t_sys_user"."user_type" IS '用户类型';
COMMENT ON COLUMN "t_sys_user"."email" IS '邮箱';
COMMENT ON COLUMN "t_sys_user"."phone_number" IS '电话';
COMMENT ON COLUMN "t_sys_user"."sex" IS '性别';
COMMENT ON COLUMN "t_sys_user"."avatar" IS '头像';
COMMENT ON COLUMN "t_sys_user"."password" IS '密码';
COMMENT ON COLUMN "t_sys_user"."status" IS '状态';
COMMENT ON COLUMN "t_sys_user"."del_flag" IS '删除标志';
COMMENT ON COLUMN "t_sys_user"."login_ip" IS '最后登录IP';
COMMENT ON COLUMN "t_sys_user"."login_date" IS '最后登录时间';
COMMENT ON COLUMN "t_sys_user"."remark" IS '备注';
COMMENT ON COLUMN "t_sys_user"."dept_id" IS '所属部门';
CREATE TABLE IF NOT EXISTS "t_sys_user_role" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "role_id" BIGINT NOT NULL REFERENCES "t_sys_role" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "t_sys_user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_t_sys_user__user_id_8e0e9b" UNIQUE ("user_id", "role_id")
);
COMMENT ON COLUMN "t_sys_user_role"."role_id" IS '角色';
COMMENT ON COLUMN "t_sys_user_role"."user_id" IS '用户';
COMMENT ON TABLE "t_sys_user_role" IS '用户角色关联表模型 - 对应t_sys_user_role表';
CREATE TABLE IF NOT EXISTS "t_sys_config" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "param_key" VARCHAR(128) NOT NULL UNIQUE,
    "param_value" TEXT,
    "param_name" VARCHAR(128) NOT NULL,
    "param_type" VARCHAR(64) NOT NULL,
    "description" TEXT,
    "is_editable" BOOL NOT NULL  DEFAULT True,
    "is_system" BOOL NOT NULL  DEFAULT False,
    "is_active" BOOL NOT NULL  DEFAULT True
);
COMMENT ON COLUMN "t_sys_config"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_config"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_config"."param_key" IS '参数键';
COMMENT ON COLUMN "t_sys_config"."param_value" IS '参数值';
COMMENT ON COLUMN "t_sys_config"."param_name" IS '参数名称';
COMMENT ON COLUMN "t_sys_config"."param_type" IS '参数类型 (string, int, boolean等)';
COMMENT ON COLUMN "t_sys_config"."description" IS '描述';
COMMENT ON COLUMN "t_sys_config"."is_editable" IS '是否允许前端编辑';
COMMENT ON COLUMN "t_sys_config"."is_system" IS '是否系统内置';
COMMENT ON COLUMN "t_sys_config"."is_active" IS '是否启用';
COMMENT ON TABLE "t_sys_config" IS '系统配置表 (新版本)';
CREATE TABLE IF NOT EXISTS "t_sys_dict_type" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "type_code" VARCHAR(64) NOT NULL UNIQUE,
    "type_name" VARCHAR(128) NOT NULL,
    "description" TEXT
);
COMMENT ON COLUMN "t_sys_dict_type"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_dict_type"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_dict_type"."type_code" IS '字典类型编码';
COMMENT ON COLUMN "t_sys_dict_type"."type_name" IS '字典类型名称';
COMMENT ON COLUMN "t_sys_dict_type"."description" IS '描述';
COMMENT ON TABLE "t_sys_dict_type" IS '系统字典类型表';
CREATE TABLE IF NOT EXISTS "t_sys_dict_data" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "data_label" VARCHAR(128) NOT NULL,
    "data_value" VARCHAR(128) NOT NULL,
    "sort_order" INT NOT NULL  DEFAULT 0,
    "description" TEXT,
    "is_enabled" BOOL NOT NULL  DEFAULT True,
    "dict_type_id" BIGINT NOT NULL REFERENCES "t_sys_dict_type" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_t_sys_dict__dict_ty_128b8b" UNIQUE ("dict_type_id", "data_value")
);
COMMENT ON COLUMN "t_sys_dict_data"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_sys_dict_data"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_sys_dict_data"."data_label" IS '字典数据标签';
COMMENT ON COLUMN "t_sys_dict_data"."data_value" IS '字典数据值';
COMMENT ON COLUMN "t_sys_dict_data"."sort_order" IS '排序';
COMMENT ON COLUMN "t_sys_dict_data"."description" IS '描述';
COMMENT ON COLUMN "t_sys_dict_data"."is_enabled" IS '是否启用';
COMMENT ON COLUMN "t_sys_dict_data"."dict_type_id" IS '字典类型ID';
COMMENT ON TABLE "t_sys_dict_data" IS '系统字典数据表';
CREATE TABLE IF NOT EXISTS "t_ai_analysis" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "analysis_name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "analysis_type" VARCHAR(50) NOT NULL,
    "algorithm" VARCHAR(100) NOT NULL,
    "parameters" JSONB NOT NULL,
    "data_sources" JSONB NOT NULL,
    "data_filters" JSONB NOT NULL,
    "status" VARCHAR(9) NOT NULL  DEFAULT 'pending',
    "progress" INT NOT NULL  DEFAULT 0,
    "result_data" JSONB,
    "insights" JSONB,
    "recommendations" JSONB,
    "started_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "error_message" TEXT,
    "is_scheduled" BOOL NOT NULL  DEFAULT False,
    "schedule_config" JSONB,
    "next_run_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" BIGINT,
    "updated_by" BIGINT
);
COMMENT ON COLUMN "t_ai_analysis"."analysis_name" IS '分析名称';
COMMENT ON COLUMN "t_ai_analysis"."description" IS '分析描述';
COMMENT ON COLUMN "t_ai_analysis"."analysis_type" IS '分析类型';
COMMENT ON COLUMN "t_ai_analysis"."algorithm" IS '分析算法';
COMMENT ON COLUMN "t_ai_analysis"."parameters" IS '分析参数(JSON)';
COMMENT ON COLUMN "t_ai_analysis"."data_sources" IS '数据源列表(JSON)';
COMMENT ON COLUMN "t_ai_analysis"."data_filters" IS '数据过滤条件(JSON)';
COMMENT ON COLUMN "t_ai_analysis"."status" IS '分析状态';
COMMENT ON COLUMN "t_ai_analysis"."progress" IS '执行进度(0-100)';
COMMENT ON COLUMN "t_ai_analysis"."result_data" IS '分析结果(JSON)';
COMMENT ON COLUMN "t_ai_analysis"."insights" IS '洞察信息(JSON)';
COMMENT ON COLUMN "t_ai_analysis"."recommendations" IS '建议信息(JSON)';
COMMENT ON COLUMN "t_ai_analysis"."started_at" IS '开始时间';
COMMENT ON COLUMN "t_ai_analysis"."completed_at" IS '完成时间';
COMMENT ON COLUMN "t_ai_analysis"."error_message" IS '错误信息';
COMMENT ON COLUMN "t_ai_analysis"."is_scheduled" IS '是否定时分析';
COMMENT ON COLUMN "t_ai_analysis"."schedule_config" IS '定时配置(JSON)';
COMMENT ON COLUMN "t_ai_analysis"."next_run_at" IS '下次运行时间';
COMMENT ON COLUMN "t_ai_analysis"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_ai_analysis"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_ai_analysis"."created_by" IS '创建人ID';
COMMENT ON COLUMN "t_ai_analysis"."updated_by" IS '更新人ID';
COMMENT ON TABLE "t_ai_analysis" IS 'AI智能分析表';
CREATE TABLE IF NOT EXISTS "t_ai_annotation_projects" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "project_name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "annotation_type" VARCHAR(50) NOT NULL,
    "data_type" VARCHAR(50) NOT NULL,
    "label_schema" JSONB NOT NULL,
    "total_samples" INT NOT NULL  DEFAULT 0,
    "annotated_samples" INT NOT NULL  DEFAULT 0,
    "reviewed_samples" INT NOT NULL  DEFAULT 0,
    "status" VARCHAR(11) NOT NULL  DEFAULT 'created',
    "progress" DOUBLE PRECISION NOT NULL  DEFAULT 0,
    "quality_threshold" DOUBLE PRECISION NOT NULL  DEFAULT 0.8,
    "inter_annotator_agreement" DOUBLE PRECISION,
    "import_config" JSONB,
    "export_config" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" BIGINT,
    "updated_by" BIGINT
);
COMMENT ON COLUMN "t_ai_annotation_projects"."project_name" IS '项目名称';
COMMENT ON COLUMN "t_ai_annotation_projects"."description" IS '项目描述';
COMMENT ON COLUMN "t_ai_annotation_projects"."annotation_type" IS '标注类型';
COMMENT ON COLUMN "t_ai_annotation_projects"."data_type" IS '数据类型';
COMMENT ON COLUMN "t_ai_annotation_projects"."label_schema" IS '标签模式(JSON)';
COMMENT ON COLUMN "t_ai_annotation_projects"."total_samples" IS '总样本数';
COMMENT ON COLUMN "t_ai_annotation_projects"."annotated_samples" IS '已标注样本数';
COMMENT ON COLUMN "t_ai_annotation_projects"."reviewed_samples" IS '已审核样本数';
COMMENT ON COLUMN "t_ai_annotation_projects"."status" IS '项目状态';
COMMENT ON COLUMN "t_ai_annotation_projects"."progress" IS '完成进度(0-100)';
COMMENT ON COLUMN "t_ai_annotation_projects"."quality_threshold" IS '质量阈值';
COMMENT ON COLUMN "t_ai_annotation_projects"."inter_annotator_agreement" IS '标注者间一致性';
COMMENT ON COLUMN "t_ai_annotation_projects"."import_config" IS '导入配置(JSON)';
COMMENT ON COLUMN "t_ai_annotation_projects"."export_config" IS '导出配置(JSON)';
COMMENT ON COLUMN "t_ai_annotation_projects"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_ai_annotation_projects"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_ai_annotation_projects"."created_by" IS '创建人ID';
COMMENT ON COLUMN "t_ai_annotation_projects"."updated_by" IS '更新人ID';
COMMENT ON TABLE "t_ai_annotation_projects" IS 'AI数据标注项目表';
CREATE TABLE IF NOT EXISTS "t_ai_health_scores" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "score_name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "target_type" VARCHAR(50) NOT NULL,
    "target_id" BIGINT NOT NULL,
    "scoring_algorithm" VARCHAR(100) NOT NULL,
    "weight_config" JSONB NOT NULL,
    "threshold_config" JSONB NOT NULL,
    "overall_score" DOUBLE PRECISION,
    "dimension_scores" JSONB,
    "risk_level" VARCHAR(20),
    "status" VARCHAR(11) NOT NULL  DEFAULT 'calculating',
    "calculated_at" TIMESTAMPTZ,
    "data_period_start" TIMESTAMPTZ,
    "data_period_end" TIMESTAMPTZ,
    "trend_direction" VARCHAR(20),
    "trend_confidence" DOUBLE PRECISION,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" BIGINT,
    "updated_by" BIGINT
);
COMMENT ON COLUMN "t_ai_health_scores"."score_name" IS '评分名称';
COMMENT ON COLUMN "t_ai_health_scores"."description" IS '评分描述';
COMMENT ON COLUMN "t_ai_health_scores"."target_type" IS '评分对象类型';
COMMENT ON COLUMN "t_ai_health_scores"."target_id" IS '评分对象ID';
COMMENT ON COLUMN "t_ai_health_scores"."scoring_algorithm" IS '评分算法';
COMMENT ON COLUMN "t_ai_health_scores"."weight_config" IS '权重配置(JSON)';
COMMENT ON COLUMN "t_ai_health_scores"."threshold_config" IS '阈值配置(JSON)';
COMMENT ON COLUMN "t_ai_health_scores"."overall_score" IS '总体评分(0-100)';
COMMENT ON COLUMN "t_ai_health_scores"."dimension_scores" IS '维度评分(JSON)';
COMMENT ON COLUMN "t_ai_health_scores"."risk_level" IS '风险等级';
COMMENT ON COLUMN "t_ai_health_scores"."status" IS '评分状态';
COMMENT ON COLUMN "t_ai_health_scores"."calculated_at" IS '计算时间';
COMMENT ON COLUMN "t_ai_health_scores"."data_period_start" IS '数据周期开始';
COMMENT ON COLUMN "t_ai_health_scores"."data_period_end" IS '数据周期结束';
COMMENT ON COLUMN "t_ai_health_scores"."trend_direction" IS '趋势方向';
COMMENT ON COLUMN "t_ai_health_scores"."trend_confidence" IS '趋势置信度';
COMMENT ON COLUMN "t_ai_health_scores"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_ai_health_scores"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_ai_health_scores"."created_by" IS '创建人ID';
COMMENT ON COLUMN "t_ai_health_scores"."updated_by" IS '更新人ID';
COMMENT ON TABLE "t_ai_health_scores" IS 'AI健康评分表';
CREATE TABLE IF NOT EXISTS "t_ai_models" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "model_name" VARCHAR(200) NOT NULL,
    "model_version" VARCHAR(50) NOT NULL,
    "description" TEXT,
    "model_type" VARCHAR(50) NOT NULL,
    "algorithm" VARCHAR(100) NOT NULL,
    "framework" VARCHAR(50) NOT NULL,
    "model_file_path" VARCHAR(500) NOT NULL,
    "model_file_size" BIGINT,
    "model_file_hash" VARCHAR(64),
    "training_dataset" VARCHAR(200),
    "training_parameters" JSONB NOT NULL,
    "training_metrics" JSONB,
    "status" VARCHAR(8) NOT NULL  DEFAULT 'draft',
    "accuracy" DOUBLE PRECISION,
    "precision" DOUBLE PRECISION,
    "recall" DOUBLE PRECISION,
    "f1_score" DOUBLE PRECISION,
    "deployment_config" JSONB,
    "deployed_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" BIGINT,
    "updated_by" BIGINT
);
COMMENT ON COLUMN "t_ai_models"."model_name" IS '模型名称';
COMMENT ON COLUMN "t_ai_models"."model_version" IS '模型版本';
COMMENT ON COLUMN "t_ai_models"."description" IS '模型描述';
COMMENT ON COLUMN "t_ai_models"."model_type" IS '模型类型';
COMMENT ON COLUMN "t_ai_models"."algorithm" IS '算法名称';
COMMENT ON COLUMN "t_ai_models"."framework" IS '框架名称';
COMMENT ON COLUMN "t_ai_models"."model_file_path" IS '模型文件路径';
COMMENT ON COLUMN "t_ai_models"."model_file_size" IS '模型文件大小(字节)';
COMMENT ON COLUMN "t_ai_models"."model_file_hash" IS '模型文件哈希';
COMMENT ON COLUMN "t_ai_models"."training_dataset" IS '训练数据集';
COMMENT ON COLUMN "t_ai_models"."training_parameters" IS '训练参数(JSON)';
COMMENT ON COLUMN "t_ai_models"."training_metrics" IS '训练指标(JSON)';
COMMENT ON COLUMN "t_ai_models"."status" IS '模型状态';
COMMENT ON COLUMN "t_ai_models"."accuracy" IS '准确率';
COMMENT ON COLUMN "t_ai_models"."precision" IS '精确率';
COMMENT ON COLUMN "t_ai_models"."recall" IS '召回率';
COMMENT ON COLUMN "t_ai_models"."f1_score" IS 'F1分数';
COMMENT ON COLUMN "t_ai_models"."deployment_config" IS '部署配置(JSON)';
COMMENT ON COLUMN "t_ai_models"."deployed_at" IS '部署时间';
COMMENT ON COLUMN "t_ai_models"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_ai_models"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_ai_models"."created_by" IS '创建人ID';
COMMENT ON COLUMN "t_ai_models"."updated_by" IS '更新人ID';
COMMENT ON TABLE "t_ai_models" IS 'AI模型管理表';
CREATE TABLE IF NOT EXISTS "t_ai_predictions" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "prediction_name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "target_variable" VARCHAR(100) NOT NULL,
    "prediction_horizon" INT NOT NULL,
    "model_type" VARCHAR(50) NOT NULL,
    "parameters" JSONB NOT NULL,
    "data_source" VARCHAR(100) NOT NULL,
    "data_filters" JSONB NOT NULL,
    "status" VARCHAR(9) NOT NULL  DEFAULT 'pending',
    "progress" INT NOT NULL  DEFAULT 0,
    "result_data" JSONB,
    "accuracy_score" DOUBLE PRECISION,
    "confidence_interval" JSONB,
    "started_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "error_message" TEXT,
    "export_formats" JSONB NOT NULL,
    "shared_with" JSONB NOT NULL,
    "is_public" BOOL NOT NULL  DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" BIGINT,
    "updated_by" BIGINT
);
COMMENT ON COLUMN "t_ai_predictions"."prediction_name" IS '预测名称';
COMMENT ON COLUMN "t_ai_predictions"."description" IS '预测描述';
COMMENT ON COLUMN "t_ai_predictions"."target_variable" IS '目标变量';
COMMENT ON COLUMN "t_ai_predictions"."prediction_horizon" IS '预测时间范围(小时)';
COMMENT ON COLUMN "t_ai_predictions"."model_type" IS '模型类型';
COMMENT ON COLUMN "t_ai_predictions"."parameters" IS '预测参数(JSON)';
COMMENT ON COLUMN "t_ai_predictions"."data_source" IS '数据源';
COMMENT ON COLUMN "t_ai_predictions"."data_filters" IS '数据过滤条件(JSON)';
COMMENT ON COLUMN "t_ai_predictions"."status" IS '预测状态';
COMMENT ON COLUMN "t_ai_predictions"."progress" IS '执行进度(0-100)';
COMMENT ON COLUMN "t_ai_predictions"."result_data" IS '预测结果数据(JSON)';
COMMENT ON COLUMN "t_ai_predictions"."accuracy_score" IS '准确率分数';
COMMENT ON COLUMN "t_ai_predictions"."confidence_interval" IS '置信区间(JSON)';
COMMENT ON COLUMN "t_ai_predictions"."started_at" IS '开始时间';
COMMENT ON COLUMN "t_ai_predictions"."completed_at" IS '完成时间';
COMMENT ON COLUMN "t_ai_predictions"."error_message" IS '错误信息';
COMMENT ON COLUMN "t_ai_predictions"."export_formats" IS '支持的导出格式';
COMMENT ON COLUMN "t_ai_predictions"."shared_with" IS '分享给的用户列表';
COMMENT ON COLUMN "t_ai_predictions"."is_public" IS '是否公开';
COMMENT ON COLUMN "t_ai_predictions"."created_at" IS '创建时间';
COMMENT ON COLUMN "t_ai_predictions"."updated_at" IS '更新时间';
COMMENT ON COLUMN "t_ai_predictions"."created_by" IS '创建人ID';
COMMENT ON COLUMN "t_ai_predictions"."updated_by" IS '更新人ID';
COMMENT ON TABLE "t_ai_predictions" IS 'AI趋势预测表';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "t_sys_role_menu" (
    "menu_id" BIGINT NOT NULL REFERENCES "t_sys_role" ("id") ON DELETE CASCADE,
    "role_id" BIGINT NOT NULL REFERENCES "t_sys_menu" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_t_sys_role__menu_id_90608e" ON "t_sys_role_menu" ("menu_id", "role_id");
CREATE TABLE IF NOT EXISTS "t_sys_role_api" (
    "api_id" BIGINT NOT NULL REFERENCES "t_sys_role" ("id") ON DELETE CASCADE,
    "role_id" BIGINT NOT NULL REFERENCES "t_sys_api_endpoints" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_t_sys_role__api_id_0bd2fa" ON "t_sys_role_api" ("api_id", "role_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
