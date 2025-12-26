from app.settings.config import settings

broker_url = settings.celery.broker_url
result_backend = settings.celery.result_backend
task_serializer = settings.celery.task_serializer
result_serializer = settings.celery.result_serializer
accept_content = settings.celery.accept_content
timezone = settings.celery.timezone
enable_utc = settings.celery.enable_utc

# 任务路由
task_routes = {
    'app.services.ai.tasks.train_model': {'queue': 'ai_training'},
    'app.services.ai.tasks.evaluate_model': {'queue': 'ai_evaluation'},
}

# 任务限流
task_annotations = {
    'app.services.ai.tasks.train_model': {'rate_limit': '10/m'}
}
