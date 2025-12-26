from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_serializer


class CredentialsSchema(BaseModel):
    username: str = Field(..., description="用户名称", example="admin")
    password: str = Field(..., description="密码", example="123456")


class RefreshTokenSchema(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌过期时间（秒）")
    expires_at: str = Field(..., description="访问令牌过期时间（ISO格式）")
    refresh_expires_in: int = Field(..., description="刷新令牌过期时间（秒）")
    refresh_expires_at: str = Field(..., description="刷新令牌过期时间（ISO格式）")


class JWTOut(BaseModel):
    access_token: str
    username: str


class JWTPayload(BaseModel):
    user_id: int
    username: str
    is_superuser: bool
    exp: datetime
    
    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """自定义序列化方法，将exp字段转换为Unix时间戳"""
        # 使用更安全的时间戳计算方式，避免时区相关的错误
        from datetime import timezone
        import calendar
        
        if self.exp.tzinfo is None:
            # 对于naive datetime，直接当作UTC时间处理
            # 使用calendar.timegm避免时区转换问题
            exp_timestamp = int(calendar.timegm(self.exp.timetuple()))
        else:
            # 对于aware datetime，转换为UTC后计算时间戳
            utc_exp = self.exp.astimezone(timezone.utc)
            exp_timestamp = int(calendar.timegm(utc_exp.timetuple()))
        
        return {
            "user_id": self.user_id,
            "username": self.username,
            "is_superuser": self.is_superuser,
            "exp": exp_timestamp
        }
