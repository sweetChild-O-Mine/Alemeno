from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class JobResponse(BaseModel):
    id: int
    status: str
    filename: str
    created_at: datetime

    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobSummaryResponse(BaseModel):
    id: int
    job_id: int
    total_spend_inr: float
    total_spend_usd: float
    top_merchants: Any
    anomaly_count: int
    narrative: Optional[str] = None
    risk_level: Optional[str] = None

    class Config:
        from_attributes = True