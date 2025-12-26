from celery import Celery
from app.core import celery_config
import os

# 设置默认环境变量
os.environ.setdefault('APP_ENV', 'dev')

app = Celery('device_monitor')
app.config_from_object(celery_config)

# 自动发现任务
app.autodiscover_tasks(['app.services.ai'])

if __name__ == '__main__':
    app.start()
