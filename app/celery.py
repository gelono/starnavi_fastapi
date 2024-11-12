from celery import Celery

# Initializing Celery
app = Celery('tasks', broker='redis://localhost:6379/0')
app.conf.result_backend = 'redis://localhost:6379/0'

# Settings for Celery
app.conf.task_routes = {
    'tasks.send_auto_reply': {'queue': 'default'},
}

app.autodiscover_tasks(['app'])

# Configuration declaration for ORM
app.conf.update(
    result_expires=3600,
    accept_content=['json'],
    result_serializer='json',
)
