import os
import time
from app.database import SessionLocal
from app import models
from celery import Celery

# get the redis url from .env
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# initialize our celery
celery_app = Celery(
    "alemeno_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer = 'json',
    timezone='UTC',
    enable_utc=True
)

# @celery_app.task is a decorator. it tells celery 
# "This function shouldn't run immediately. It should be put in the Redis queue!"
@celery_app.task(name="process_transaction_file")
def process_transaction_file(jon_id: int, file_path: str):
    # every time the worker runs a task, it needs its own temporary db connection
    db = SessionLocal()

    try:

        # find the job -> change its status to processing -> commit data in db --> print stuff on cosnole ig

        # 1. update the job status to "processing"
        job = db.query(models.Job).filter(models.Job.id == job_id).first()

        if not job:
            return "Job not found"
        
        job.status = "processing"
        db.commit()

        print("Worker started processing Job {job_id} from {file_path}")


