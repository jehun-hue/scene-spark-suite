import os
import mimetypes
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Response, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
import json
import io
import shutil
from dotenv import load_dotenv

from exporters.fcpxml import generate_fcpxml
from exporters.premiere import generate_premiere_xml
from exporters.srt import generate_srt
from exporters.zipper import create_export_zip
from exporters.thumbnails import extract_thumbnails
from editor.video_editor import render_final_short

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

from pydantic import BaseModel
class StepRequest(BaseModel):
    file_id: str | None = None
    analysis_data: dict | None = None
    script_data: dict | None = None

@app.post("/api/step/upload")
async def step_upload(file: UploadFile = File(...), x_api_key: str = Header(None)):
    temp_file_path = f"temp_{file.filename}"
    thumb_dir = f"thumbs_{file.filename}"
    try:
        client = get_client(x_api_key)
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())
        mime_type, _ = mimetypes.guess_type(temp_file_path)
        if not mime_type: mime_type = "video/mp4"
        with open(temp_file_path, "rb") as f:
            uploaded_file = client.files.upload(file=f, config=types.UploadFileConfig(mime_type=mime_type))
        max_wait, wait_interval, elapsed = 60, 3, 0
        file_status = uploaded_file
        while elapsed < max_wait:
            file_status = client.files.get(name=uploaded_file.name)
            if file_status.state.name == "ACTIVE": break
            time.sleep(wait_interval)
            elapsed += wait_interval
        if file_status.state.name != "ACTIVE":
            return {"step": 1, "status": "error", "message": "File processing timeout"}
        # Extract at least one thumbnail for UI
        os.makedirs(thumb_dir, exist_ok=True)
        thumbnails = extract_thumbnails(temp_file_path, ["00:00:00.000"], thumb_dir)
        return {"step": 1, "status": "complete", "file_id": uploaded_file.name, "message": "업로드 완료", "thumbnails": thumbnails}
    except Exception as e:
        return {"step": 1, "status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        if os.path.exists(thumb_dir): shutil.rmtree(thumb_dir)

@app.post("/api/step/analyze")
async def step_analyze(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        video_file = client.files.get(name=req.file_id)
        prompt = "이 영상의 장면을 분석하고, 객체/행위, 시네마틱 정보, 청각 정보를 추출하라. 타겟 시청자를 정의하라. 안전성을 검토하라. JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[video_file, prompt], config={"response_mime_type": "application/json"})
        return {"step": 2, "status": "complete", "data": json.loads(response.text), "message": "기본 분석 완료"}
    except Exception as e:
        return {"step": 2, "status": "error", "message": str(e)}

@app.post("/api/step/script")
async def step_script(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        video_file = client.files.get(name=req.file_id)
        prompt = f"이전 분석 결과({json.dumps(req.analysis_data)})를 기반으로 60초 숏폼 대본을 작성하라. 스토리 구조, 정보 공개 전략, 감정 곡선을 설계하라. JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[video_file, prompt], config={"response_mime_type": "application/json"})
        return {"step": 3, "status": "complete", "data": json.loads(response.text), "message": "대본 생성 완료"}
    except Exception as e:
        return {"step": 3, "status": "error", "message": str(e)}

@app.post("/api/step/titles")
async def step_titles(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        prompt = f"이전 분석({json.dumps(req.analysis_data)})과 대본({json.dumps(req.script_data)})을 기반으로 바이럴 제목 30개를 생성하고 상위 7개와 A/B/C 세트를 선정하라. JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt], config={"response_mime_type": "application/json"})
        return {"step": 4, "status": "complete", "data": json.loads(response.text), "message": "제목 생성 완료"}
    except Exception as e:
        return {"step": 4, "status": "error", "message": str(e)}

@app.post("/api/step/editpoints")
async def step_editpoints(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        video_file = client.files.get(name=req.file_id)
        prompt = f"대본({json.dumps(req.script_data)})을 기반으로 초 단위 편집 구성안(Edit Decision List)을 생성하라. 타임코드, 편집 이벤트, 자막을 포함하라. JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[video_file, prompt], config={"response_mime_type": "application/json"})
        return {"step": 5, "status": "complete", "data": json.loads(response.text), "message": "편집점 생성 완료"}
    except Exception as e:
        return {"step": 5, "status": "error", "message": str(e)}

@app.post("/api/step/variations")
async def step_variations(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        prompt = f"분석({json.dumps(req.analysis_data)}) 및 대본({json.dumps(req.script_data)})을 기반으로 4가지 감정 변주 대본(물욕/본능/감동/분노)을 생성하라. JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt], config={"response_mime_type": "application/json"})
        return {"step": 6, "status": "complete", "data": json.loads(response.text), "message": "변주 대본 완료"}
    except Exception as e:
        return {"step": 6, "status": "error", "message": str(e)}

@app.post("/api/step/keywords")
async def step_keywords(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        prompt = f"분석({json.dumps(req.analysis_data)})을 기반으로 한국어 25개 + 영어 25개 검색 키워드를 생성하라. JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt], config={"response_mime_type": "application/json"})
        return {"step": 7, "status": "complete", "data": json.loads(response.text), "message": "키워드 생성 완료"}
    except Exception as e:
        return {"step": 7, "status": "error", "message": str(e)}

@app.get("/api/test-key")
async def test_key(x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        # Simple test call
        client.models.generate_content(
            model="gemini-2.5-flash",
            contents="hi",
            config=types.GenerateContentConfig(max_output_tokens=10)
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/analyze")
async def analyze_video(file: UploadFile = File(...), x_api_key: str = Header(None)):
    temp_file_path = f"temp_{file.filename}"
    thumb_dir = f"thumbs_{file.filename}"
    try:
        client = get_client(x_api_key)
        
        # Save temp file
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        # Detect Mime Type
        mime_type, _ = mimetypes.guess_type(temp_file_path)
        if not mime_type:
            mime_type = "video/mp4"

        # Upload to Gemini
        print(f"Uploading {temp_file_path} to Gemini as {mime_type}...")
        with open(temp_file_path, "rb") as f:
            video_file = client.files.upload(
                file=f,
                config=types.UploadFileConfig(mime_type=mime_type)
            )
        print(f"Upload complete: {video_file.uri}")

        # Wait for ACTIVE state
        print(f"Waiting for file {video_file.name} to become ACTIVE...")
        max_wait = 60
        wait_interval = 3
        elapsed = 0
        file_status = video_file
        
        while elapsed < max_wait:
            file_status = client.files.get(name=video_file.name)
            if file_status.state.name == "ACTIVE":
                print(f"File is ACTIVE after {elapsed}s")
                break
            print(f"File state: {file_status.state.name}, waiting... ({elapsed}s)")
            time.sleep(wait_interval)
            elapsed += wait_interval

        if file_status.state.name != "ACTIVE":
            raise HTTPException(status_code=500, detail=f"File processing timeout. State: {file_status.state.name}")

        # Read system prompt
        prompt_content = ""
        prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_content = f.read()

        # Generate content
        print("Analyzing video content with Gemini 2.5 Flash...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[video_file, prompt_content],
            config={"response_mime_type": "application/json"}
        )

        # Parse Gemini response
        result_json = json.loads(response.text)

        # Extract thumbnails
        try:
            edit_list = result_json.get("edit_map", {}).get("edit_decision_list", [])
            timecodes = [item.get("timecode", "00:00:00.000") for item in edit_list]
            print(f"Extracting {len(timecodes)} thumbnails...")
            thumbnails = extract_thumbnails(temp_file_path, timecodes, thumb_dir)
            result_json["thumbnails"] = thumbnails
        except Exception as te:
            print(f"Thumbnail extraction failed: {str(te)}")
            result_json["thumbnails"] = []

        return result_json

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(thumb_dir):
            shutil.rmtree(thumb_dir)

@app.post("/api/render")
async def render_video(file: UploadFile = File(...), analysis: str = Form(...)):
    temp_file_path = f"render_{file.filename}"
    output_meta_path = f"final_{file.filename}.mp4"
    try:
        # Save source video
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())
            
        # Parse analysis JSON
        analysis_json = json.loads(analysis)
        
        # Render
        print("Rendering final shorts video...")
        final_path = render_final_short(temp_file_path, analysis_json, output_meta_path)
        
        if os.path.exists(final_path):
            with open(final_path, "rb") as f:
                content = f.read()
            return Response(
                content=content,
                media_type="video/mp4",
                headers={"Content-Disposition": f"attachment; filename=short_final.mp4"}
            )
        else:
            raise HTTPException(status_code=500, detail="Rendering failed to produce output")
            
    except Exception as e:
        print(f"Error during render: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(output_meta_path):
            os.remove(output_meta_path)

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
