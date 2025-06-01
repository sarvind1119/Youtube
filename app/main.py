from fastapi import FastAPI, Query, HTTPException
from app.youtube_client import get_comments
from urllib.parse import urlparse, parse_qs
from fastapi import Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from typing import Optional
from app.analysis import analyze_comments
templates = Jinja2Templates(directory="app/templates")
from fastapi.responses import FileResponse
import uuid
import os

app = FastAPI()


from fastapi.responses import StreamingResponse
import pandas as pd
import io
from enum import Enum

class ExportFormat(str, Enum):
    json = "json"
    csv = "csv"
    xlsx = "xlsx"

@app.get("/comments/export")
async def export_comments(video_url: str, format: ExportFormat = ExportFormat.json):
    video_id = extract_video_id(video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    comments = get_comments(video_id)
    if not comments or "error" in comments:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {comments.get('error')}")

    # Convert to DataFrame
    df = pd.DataFrame(comments)

    if format == "json":
        return df.to_dict(orient="records")

    elif format == "csv":
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename={video_id}_comments.csv"
        })

    elif format == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Comments")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
            "Content-Disposition": f"attachment; filename={video_id}_comments.xlsx"
        })
from urllib.parse import urlparse, parse_qs
def extract_video_id(url: str) -> str:
    parsed_url = urlparse(url)
    
    # Case: youtu.be short link
    if parsed_url.netloc in ["youtu.be"]:
        return parsed_url.path.lstrip('/')

    # Case: youtube.com/watch?v=...
    if parsed_url.netloc in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]

    return None


@app.get("/comments")
async def fetch_comments(video_url: str = Query(...)):
    video_id = extract_video_id(video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")
    
    result = get_comments(video_id)

    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {result['error']}")
    
    return {"video_id": video_id, "comments": result}


@app.get("/")
async def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/export")
async def handle_form(
    request: Request,
    video_url: str = Form(...),
    format: ExportFormat = Form(...),
    max_results: Optional[int] = Form(None)
):
    video_id = extract_video_id(video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    comments = get_comments(video_id, max_results=max_results)
    if not comments or "error" in comments:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {comments.get('error')}")

    from app.analysis import analyze_comments
    analysis = analyze_comments(comments)
    sentiment = analysis["sentiment_distribution"]
    labeled_comments = analysis["labeled_comments"]
    total = len(labeled_comments)

    df = pd.DataFrame(labeled_comments)

    # Generate unique filename prefix
    token = str(uuid.uuid4())[:8]
    base = f"temp/{video_id}_{token}"

    # Ensure folder exists
    os.makedirs("temp", exist_ok=True)

    df.to_csv(f"{base}.csv", index=False)
    df.to_excel(f"{base}.xlsx", index=False)
    df.to_json(f"{base}.json", orient="records", indent=2)

    download_links = {
        "csv": f"/download/{video_id}_{token}.csv",
        "xlsx": f"/download/{video_id}_{token}.xlsx",
        "json": f"/download/{video_id}_{token}.json"
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "video_url": video_url,
        "max_results": max_results,
        "sentiment": sentiment,
        "total_comments": total,
        "download_links": download_links
    })

@app.get("/comments/analyze")
async def analyze(video_url: str, max_results: Optional[int] = 500):
    video_id = extract_video_id(video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")
    
    comments = get_comments(video_id, max_results=max_results)
    if not comments or "error" in comments:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {comments.get('error')}")

    analysis = analyze_comments(comments)
    return {
        "video_id": video_id,
        "total_comments": len(comments),
        **analysis
    }

@app.get("/download/{filename}")
async def download_file(filename: str):
    filepath = f"temp/{filename}"
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")
