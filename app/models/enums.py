from enum import Enum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ExecutionPhase(str, Enum):
    """执行阶段枚举"""
    INIT = "init"
    PROCESS = "process"
    COMPLETE = "complete"
    ERROR = "error"


class LogCategory(str, Enum):
    """日志分类枚举"""
    EXECUTION = "execution"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"
    SECURITY = "security"
    RETRY = "retry"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
