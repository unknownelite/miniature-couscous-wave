# # Install Celery & Redis
# # pip install celery redis
# from celery import Celery
# from django.utils import timezone
# from .models import Investment

# app = Celery('golden_crypto', broker='redis://localhost:6379/0')

# @app.task
# def process_daily_interest():
#     investments = Investment.objects.filter(is_active=True)
#     for inv in investments:
#         # Your interest calculation logic here
#         pass

# # Schedule it in `settings.py`
# CELERY_BEAT_SCHEDULE = {
#     'daily-interest': {
#         'task': 'your_app.tasks.process_daily_interest',
#         'schedule': 86400,  # Runs every 24 hours
#     },
# }