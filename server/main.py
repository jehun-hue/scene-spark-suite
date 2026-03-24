import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
import json
import io
from dotenv import load_dotenv

from exporters.fcpxml import generate_fcpxml
from exporters.premiere import generate_premiere_xml
from exporters.srt import generate_srt
from exporters.zipper import create_export_zip

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client(x_api_key: str = None):
    # Use request header key if provided, fallback to environment variable
    api_key = x_api_key if x_api_key else os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="Gemini API Key missing")
    return genai.Client(api_key=api_key)

@app.get("/api/test-key")
async def test_key(x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        # Simple test call
        client.models.generate_content(
            model="gemini-2.0-flash",
            contents="hi",
            config=types.GenerateContentConfig(max_output_tokens=10)
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/analyze")
async def analyze_video(file: UploadFile = File(...), x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        
        # Save temp file
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        # Upload to Gemini
        print(f"Uploading {temp_file_path} to Gemini...")
        video_file = client.files.upload(path=temp_file_path)
        print(f"Upload complete: {video_file.uri}")

        # Read system prompt
        prompt_content = ""
        prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_content = f.read()

        # Generate content
        print("Analyzing video content with Gemini 2.0 Flash...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[video_file, prompt_content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )

        # Clean up temp file
        os.remove(temp_file_path)

        # Return the response JSON
        return json.loads(response.text)

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/fcpxml")
async def export_fcpxml(data: dict):
    fcpxml_str = generate_fcpxml(data)
    return Response(content=fcpxml_str, media_type="application/xml", 
                    headers={"Content-Disposition": "attachment; filename=project.fcpxml"})

@app.post("/api/export/premiere")
async def export_premiere(data: dict):
    xml_str = generate_premiere_xml(data)
    return Response(content=xml_str, media_type="application/xml", 
                    headers={"Content-Disposition": "attachment; filename=project.xml"})

@app.post("/api/export/srt")
async def export_srt(data: dict):
    srt_str = generate_srt(data)
    return Response(content=srt_str, media_type="text/plain", 
                    headers={"Content-Disposition": "attachment; filename=subtitles.srt"})

@app.post("/api/export/zip")
async def export_zip(data: dict):
    fcp = generate_fcpxml(data)
    pre = generate_premiere_xml(data)
    srt = generate_srt(data)
    zip_bytes = create_export_zip(fcp, pre, srt)
    return Response(content=zip_bytes, media_type="application/zip", 
                    headers={"Content-Disposition": "attachment; filename=scene-spark-export.zip"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
