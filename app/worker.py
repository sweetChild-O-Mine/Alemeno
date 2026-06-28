
import os
import time
from app.database import SessionLocal
from app import models
from celery import Celery
import pandas as pd 
from google import genai
import os

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
def process_transaction_file(job_id: int, file_path: str):
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

        print(f"Worker started processing Job {job_id} from {file_path}")

        # 2. FAKE DELAY: we will sleep for 10 seconds to simulate heavy data processing
        # in the next step we will replace this with padas and gemini 
        print(f"Reading CSV file with Pandas")

        # read the fkin file and turn it into dataframe
        df = pd.read_csv(file_path)
        
        # find out the lenght or no. of rows in that table
        raw_count = len(df)

        print(f"I just read a CSV with {raw_count} rows!!!")

        # start the data cleaning
        # DROP the row that donnt have a merchahnt or an amount
        # using the fucniton  dropna (drop Not Available/Null).
        # Look ONLY at these two columns. If either of them is blank (NaN), delete the entire row from the df table."
        df = df.dropna(subset = ['merchant', 'amount'])

        # Data Cleanign : convert the amount to numbers and remove $ signs or commmmas
        # we force it to be mumeric and if there are weird errors , coerce turns them to NaN
        df['amount'] = pd.to_numeric(df['amount'].replace('[\$,]', '', regex=True), errors='coerce')
        
        # Clean the date column so PostgreSQL doesn't crash on DD-MM-YYYY formats
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # now drop the rows who got NaN in their Amount or date column
        df = df.dropna(subset=['amount', 'date'])

        clean_count = len(df)

        print(f"After cleaning, we have  {clean_count} valid rows left")


        # STEP 3 save the clean transaction to our db
        print(f"Saving {clean_count} clean transaction to PostgreSQL...")

        # convert the pandas DataFrame into a list of python directories 
        records = df.to_dict('records')

        # we loop thorugh our list of dictionaries and save them one by one (for massive datasets we would use bulk_insert, for this is fine for now)
        for row in records:
            # anomaly logic: if sepnd is greateer than 1000, flag it as True
            is_anomaly = True if row['amount'] > 1000 else False

            # Create a new row for the PostgreSQL Transaction table
            transaction = models.Transaction(
                job_id=job_id,
                txn_id=str(row.get('txn_id', '')),
                merchant=str(row['merchant']),
                amount=float(row["amount"]),
                currency=str(row.get('currency', 'USD')),
                date=row['date'].to_pydatetime() if pd.notna(row['date']) else None,
                is_anomaly=is_anomaly
            )

            # add it to the waiting room
            db.add(transaction)
        
        # update the origianl job table withour final counts
        job.row_count_raw = raw_count
        job.row_count_clean = clean_count

        # save everythgn in the waiting room to the dv permanently
        db.commit()
        print("Transaction saved succesffully")

        # GEMINI STUFF
        print("Asking Gemini AI to anaylyze the spending...")

        # 1. Inititalizez the gemini client using the api key from our .env file

        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        # 2. build our prompt using a multi-line f-string
        # we tell the AI exactly what happened
        prompt = f"""
        You are a financial analyst. I just processed a user's credit card statement.
        - Total raw transactions: {raw_count}
        - Valid clean transactions: {clean_count}
        
        Based on this limited data, give me a 2-sentence summary of their spending behavior.
        Also, assign a risk level (Low, Medium, or High).
        Format your response like this:
        Narrative: [your 2 sentences]
        Risk: [Low/Medium/High]
        """

        # 3 send the prompt to the ai 
        # this makes a network request to Google's servers
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        ai_text = response.text
        print("_____GEMINI SAYS_______")
        print(ai_text)

        # 4. Save the summary to the database!
        summary = models.JobSummary(
            job_id=job_id,
            narrative=ai_text,
            risk_level="Unknown" # You can parse this out later if you want!
        )
        db.add(summary)
        db.commit()

        # 3. mark the job as completed
        job.status = "completed"
        db.commit()

        print(f"Worker finished the processign job {job_id}")
    
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        print(f"Worker failed: {e}")

    finally:
        # always close the db connection when the task finishes to prevent memory leaks
        db.close()
