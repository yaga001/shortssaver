from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import io

app = FastAPI()

# CORS (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/info")
async def get_video_info(req: Request):
    data = await req.json()
    url = data.get("url")

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'force_generic_extractor': False,
        'noplaylist': True,
        'extract_flat': False,
        'simulate': True,
        'format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.youtube.com'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", ""),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "views": info.get("view_count", 0),
                "download_url": info.get("url", "")
            }
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/api/download")
async def download_video(req: Request):
    data = await req.json()
    url = data.get("url")

    ydl_opts = {
        'quiet': True,
        'format': 'mp4',
        'outtmpl': '-',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.youtube.com'
        }
    }

    buffer = io.BytesIO()
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            ydl.download([url])

            stream_url = result.get('url')
            return StreamingResponse(
                ydl.urlopen(stream_url),
                media_type="video/mp4",
                headers={"Content-Disposition": f"attachment; filename=\"{result['title']}.mp4\""}
            )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/api/bulk")
async def bulk_list(req: Request):
    data = await req.json()
    url = data.get("url")

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': 50,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.youtube.com'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info.get("entries", [])
            videos = []
            for entry in entries:
                if 'url' in entry:
                    videos.append({
                        "title": entry.get("title", "video"),
                        "url": f"https://www.youtube.com/watch?v={entry['id']}"
                    })
            return {"videos": videos}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
