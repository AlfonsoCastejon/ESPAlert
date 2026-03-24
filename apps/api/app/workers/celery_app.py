import os
from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

redis_url = str(settings.REDIS_URL)

celery_app = Celery(
    'espalert',
    broker=redis_url,
    backend=redis_url,
    include=['app.workers.tasks'],
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Madrid',
    enable_utc=True,
    task_track_started=True,
)

celery_app.conf.beat_schedule = {
    'fetch-aemet-every-5-mins': {
        'task': 'app.workers.tasks.fetch_aemet_task',
        'schedule': crontab(minute='*/5'),
    },
    'fetch-ign-every-2-mins': {
        'task': 'app.workers.tasks.fetch_ign_task',
        'schedule': crontab(minute='*/2'),
    },
    'fetch-dgt-every-5-mins': {
        'task': 'app.workers.tasks.fetch_dgt_task',
        'schedule': crontab(minute='*/5'),
    },
    'fetch-meteoalarm-every-5-mins': {
        'task': 'app.workers.tasks.fetch_meteoalarm_task',
        'schedule': crontab(minute='*/5'),
    },
    'expire-alerts-every-10-mins': {
        'task': 'app.workers.tasks.expire_alerts_task',
        'schedule': crontab(minute='*/10'),
    },
}
