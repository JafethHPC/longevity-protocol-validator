"""
Report API Routes

FastAPI routes for generating and querying research reports.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import Dict
import json
import asyncio

from app.schemas.report import ReportRequest, FollowUpRequest, ResearchReport
from app.services.report import generate_report, generate_followup_answer
from app.services.pdf_export import generate_report_pdf

router = APIRouter(prefix="/api/reports", tags=["reports"])

# In-memory cache for reports (in production, use Redis or database)
_report_cache: Dict[str, ResearchReport] = {}


@router.post("/generate", response_model=ResearchReport)
async def create_report(request: ReportRequest):
    """
    Generate a new research report for a given question.
    Returns a structured report with findings, protocols, and sources.
    """
    try:
        report = generate_report(
            question=request.question,
            max_sources=request.max_sources
        )
        
        # Cache the report for follow-up questions
        _report_cache[report.id] = report
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stream")
async def create_report_stream(request: ReportRequest):
    """
    Generate a report with streaming progress updates.
    Sends Server-Sent Events with status updates during generation.
    """
    async def event_generator():
        try:
            # Send initial status
            yield f"event: status\ndata: {json.dumps({'message': 'Searching scientific databases...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Generate the report (this is synchronous, but we wrap it)
            loop = asyncio.get_event_loop()
            report = await loop.run_in_executor(
                None,
                lambda: generate_report(request.question, request.max_sources)
            )
            
            # Cache it
            _report_cache[report.id] = report
            
            # Send the complete report
            yield f"event: report\ndata: {report.model_dump_json()}\n\n"
            
            # Send completion
            yield f"event: complete\ndata: {json.dumps({'report_id': report.id})}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.get("/{report_id}", response_model=ResearchReport)
async def get_report(report_id: str):
    """
    Retrieve a previously generated report by ID.
    """
    if report_id not in _report_cache:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return _report_cache[report_id]


@router.post("/{report_id}/followup")
async def ask_followup(report_id: str, request: FollowUpRequest):
    """
    Ask a follow-up question about an existing report.
    Uses the report's sources to answer.
    """
    if report_id not in _report_cache:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = _report_cache[report_id]
    
    try:
        answer = generate_followup_answer(report, request.question)
        return {
            "question": request.question,
            "answer": answer,
            "report_id": report_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_reports():
    """
    List all cached reports (basic info only).
    """
    return [
        {
            "id": r.id,
            "question": r.question,
            "generated_at": r.generated_at.isoformat(),
            "papers_used": r.papers_used
        }
        for r in _report_cache.values()
    ]


@router.get("/{report_id}/export/pdf")
async def export_report_pdf(report_id: str):
    """
    Export a report as a styled PDF document.
    """
    if report_id not in _report_cache:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = _report_cache[report_id]
    
    try:
        pdf_bytes = generate_report_pdf(report)
        
        # Create safe filename - remove special characters, limit length
        safe_chars = []
        for c in report.question[:40]:
            if c.isalnum():
                safe_chars.append(c)
            elif c in ' -_':
                safe_chars.append('_')
        safe_filename = ''.join(safe_chars).strip('_')
        if not safe_filename:
            safe_filename = "research_report"
        filename = f"Research_Report_{safe_filename}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf",
                "Content-Length": str(len(pdf_bytes))
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

