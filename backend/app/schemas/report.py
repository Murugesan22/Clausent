from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.analysis import AnalysisResultResponse

class ReportExportMetadata(BaseModel):
    analysis_id: str
    filename: str
    export_format: str
    generated_at: datetime
    download_url: str

class ReportJSONResponse(BaseModel):
    report_metadata: ReportExportMetadata
    analysis: AnalysisResultResponse
