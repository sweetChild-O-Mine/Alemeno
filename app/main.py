from app.database import get_db
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import engine, Base
from app import models, schemas
from typing import Optional
from app.worker import process_transaction_file

# create tbale in postgres
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Alemeno Transaction Pipeline")

@app.get('/')
def read_root():
    return {"message": "Welcome to the Alemeno API! The Database is connected!"}

@app.post('/jobs/upload', response_model=schemas.JobResponse)
def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. validate that they actually
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only CSV files are allowed')

    # the 2nd step
    db_job = models.Job(filename=file.filename)
    db.add(db_job)  
    db.commit() 
    db.refresh(db_job)

    # 3. save the uploaded file to our local disk so the celery worker can read it later
    import os
    os.makedirs("/app/uploads", exist_ok=True)
    file_path = f"/app/uploads/{db_job.id}_{file.filename}"
    with open(file_path, 'wb') as buffer:
        buffer.write(file.file.read())

    # tell Celery to start processing it in the background
    # .delay() is the magic Celery fucntion that pushes it to Redis instead of running it instatntly
    process_transaction_file.delay(db_job.id, file_path)

    return db_job

@app.get("/jobs/{job_id}/status")
def get_job_status(job_id: int, db: Session = Depends(get_db)):

    job = db.query(models.Job).filter(models.Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job_id,
        "status": job.status,
    }

    if job.status == "completed":
        summary = db.query(models.JobSummary).filter(models.JobSummary.job_id == job_id).first()
        if summary:
            response["summary"] = summary
        
    return response


@app.get("/jobs/{job_id}/results")
def get_job_results(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {
        "job_id": job.id,
        "status": job.status,
    }
    
    # Get all transactions for this job
    transactions = db.query(models.Transaction).filter(models.Transaction.job_id == job_id).all()
    response["transactions"] = transactions
    
    # Get the AI summary
    summary = db.query(models.JobSummary).filter(models.JobSummary.job_id == job_id).first()
    if summary:
        response["summary"] = summary
        
    return response


# route 2 : get a list of all job 
@app.get('/jobs',  response_model=list[schemas.JobResponse])
def list_jobs(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Job)

    if status:
        query = query.filter(models.Job.status == status)

    # .all() executes the query and return the list
    jobs = query.all()
    return jobs
