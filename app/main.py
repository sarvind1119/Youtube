from fastapi import FastAPI, Query, HTTPException
from app.youtube_client import get_comments
from urllib.parse import urlparse, parse_qs
from fastapi import Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

templates = Jinja2Templates(directory="app/templates")

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
async def handle_form(request: Request, video_url: str = Form(...), format: ExportFormat = Form(...)):
    video_id = extract_video_id(video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    comments = get_comments(video_id)
    if not comments or "error" in comments:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {comments.get('error')}")

    df = pd.DataFrame(comments)

    if format == "csv":
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename={video_id}_comments.csv"
        })

    elif format == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
            "Content-Disposition": f"attachment; filename={video_id}_comments.xlsx"
        })

    elif format == "json":
        return df.to_dict(orient="records")