import uvicorn
import asyncio
from uvicorn.config import LOGGING_CONFIG
from app.core.init_app import init_data
from app.settings.config import settings

if __name__ == "__main__":
    # 使用 127.0.0.1 而不是 0.0.0.0 来避免权限问题
    print(f"Starting server on port {settings.PORT}")
    print(f"Uvicorn will attempt to bind to 127.0.0.1:{settings.PORT}")
    uvicorn.run("app:app", host="127.0.0.1", port=settings.PORT, reload=False)
