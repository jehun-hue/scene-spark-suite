import os
import mimetypes
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Response, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from google import genai
from google.genai import types
import json
import re
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

def load_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def safe_parse_json(text):
    """Gemini 응답에서 JSON을 안전하게 추출하여 파싱"""
    import re
    
    # 1단계: 마크다운 코드블록 제거
    cleaned = text.strip()
    cleaned = re.sub(r'^```json\s*\n?', '', cleaned)
    cleaned = re.sub(r'^```\s*\n?', '', cleaned)
    cleaned = re.sub(r'\n?\s*```$', '', cleaned)
    cleaned = cleaned.strip()
    
    # 2단계: 그대로 파싱 시도
    try:
        return json.loads(cleaned)
    except:
        pass
    
    # 3단계: JSON 객체/배열 범위 추출
    start = -1
    for i, c in enumerate(cleaned):
        if c in ('{', '['):
            start = i
            break
    
    if start != -1:
        bracket = cleaned[start]
        close = '}' if bracket == '{' else ']'
        depth = 0
        end_pos = -1
        in_string = False
        escape_next = False
        
        for i in range(start, len(cleaned)):
            ch = cleaned[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == bracket:
                depth += 1
            elif ch == close:
                depth -= 1
            if depth == 0:
                end_pos = i
                break
        
        if end_pos != -1:
            json_str = cleaned[start:end_pos + 1]
            try:
                return json.loads(json_str)
            except:
                # 4단계: 일반적인 JSON 오류 수정 시도
                # trailing comma 제거
                fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
                # 작은따옴표를 큰따옴표로
                # NaN, Infinity 처리
                fixed = fixed.replace(': NaN', ': null')
                fixed = fixed.replace(': Infinity', ': null')
                fixed = fixed.replace(': -Infinity', ': null')
                try:
                    return json.loads(fixed)
                except:
                    pass
                
                # 5단계: 줄 단위로 잘라서 시도
                lines = json_str.split('\n')
                for cut in range(len(lines), 0, -1):
                    attempt = '\n'.join(lines[:cut])
                    # 닫히지 않은 브래킷 보정
                    open_braces = attempt.count('{') - attempt.count('}')
                    open_brackets = attempt.count('[') - attempt.count(']')
                    attempt += ']' * open_brackets + '}' * open_braces
                    attempt = re.sub(r',\s*([}\]])', r'\1', attempt)
                    try:
                        return json.loads(attempt)
                    except:
                        continue
    
    # 최종 fallback
    return json.loads(cleaned)

def normalize_result(raw):
    """Gemini 응답의 키를 고정된 영어 키로 정규화"""
    if not isinstance(raw, dict):
        return raw

    # 키 매핑 규칙: (고정 키, 매칭 키워드 목록)
    KEY_MAP = [
        ("viral_dashboard",        ["바이럴", "viral", "대시보드", "dashboard"]),
        ("channel_safety",         ["채널", "channel", "안전", "safety", "community"]),
        ("revenue_risk",           ["수익", "profit", "revenue", "리스크", "risk", "monetization", "광고"]),
        ("target",                 ["타겟", "target"]),
        ("deep_dive_report",       ["심층", "deep_dive", "보고서", "report"]),
        ("production",             ["production", "프로덕션", "blueprint", "블루프린트"]),
        ("edit_decision_list",     ["edit_decision", "편집점", "edl"]),
        ("edit_map",               ["edit_map", "edit_engineering", "편집_설계"]),
        ("emotional_variations",   ["emotional", "감정_변주", "variation"]),
        ("search_keywords",        ["keyword", "키워드", "search", "검색", "supplementary"]),
        ("optimization",           ["optimization", "최적화", "recommendation", "추천"]),
        ("thumbnails",             ["thumbnail", "썸네일"]),
    ]

    normalized = {}
    used_keys = set()

    for fixed_key, patterns in KEY_MAP:
        for raw_key in raw:
            if raw_key in used_keys:
                continue
            raw_lower = raw_key.lower().replace(" ", "").replace("_", "")
            for p in patterns:
                if p.lower().replace("_", "") in raw_lower:
                    normalized[fixed_key] = raw[raw_key]
                    used_keys.add(raw_key)
                    break
            if fixed_key in normalized:
                break

    # 매핑 안 된 키는 그대로 유지
    for raw_key in raw:
        if raw_key not in used_keys:
            normalized[raw_key] = raw[raw_key]

    return normalized

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
        
        # Save for auto_edit
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(persisted_temp_dir, exist_ok=True)
        persisted_video_path = os.path.join(persisted_temp_dir, f"last_video_{file.filename}")
        shutil.copy2(temp_file_path, persisted_video_path)

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
        full_prompt = load_prompt()
        section_prompt = full_prompt + "\n\n[이번 단계 지시] 위 프로토콜 중 LAYER 0~3(절대 원칙, 바이럴 엔진, 타겟 설정, 영상 해부, 안전 검증)을 수행하라. analysis_metadata, target, video_dissection, safety, viral_dashboard 필드를 JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[video_file, section_prompt], config={"response_mime_type": "application/json"})
        result_data = safe_parse_json(response.text)
        
        # 분석 결과 저장 (render에서 사용)
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(persisted_temp_dir, exist_ok=True)
        with open(os.path.join(persisted_temp_dir, "last_result.json"), "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False)
            
        return {"step": 2, "status": "complete", "data": result_data, "message": "기본 분석 완료"}
    except Exception as e:
        return {"step": 2, "status": "error", "message": str(e)}

@app.post("/api/step/script")
async def step_script(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        video_file = client.files.get(name=req.file_id)
        full_prompt = load_prompt()
        section_prompt = full_prompt + "\n\n[이번 단계 지시] 이전 분석 결과: " + json.dumps(req.analysis_data, ensure_ascii=False) + "\n위 프로토콜 중 LAYER 4의 심층 조사 보고서, 스토리 구조, 정보 공개 전략, 감정 곡선, 최종 대본(5중 검증 포함)을 수행하라. deep_dive_report, production 필드를 JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[video_file, section_prompt], config={"response_mime_type": "application/json"})
        result_data = safe_parse_json(response.text)
        
        # 분석 결과 저장 (이전 결과와 병합하여 저장하는 것이 좋으나, 여기선 단순 교체)
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(persisted_temp_dir, exist_ok=True)
        # 기존 결과가 있으면 병합
        last_res_path = os.path.join(persisted_temp_dir, "last_result.json")
        final_save_data = result_data
        if os.path.exists(last_res_path):
            try:
                with open(last_res_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                old_data.update(result_data)
                final_save_data = old_data
            except: pass
        with open(last_res_path, "w", encoding="utf-8") as f:
            json.dump(final_save_data, f, ensure_ascii=False)

        return {"step": 3, "status": "complete", "data": result_data, "message": "대본 생성 완료"}
    except Exception as e:
        return {"step": 3, "status": "error", "message": str(e)}

@app.post("/api/step/titles")
async def step_titles(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        full_prompt = load_prompt()
        section_prompt = full_prompt + "\n\n[이번 단계 지시] 이전 분석: " + json.dumps(req.analysis_data, ensure_ascii=False) + "\n대본: " + json.dumps(req.script_data, ensure_ascii=False) + "\n위 프로토콜 중 LAYER 4의 바이럴 제목 V.4.0(8대 법칙, 안티패턴 필터링, Thumb-Stop 시뮬레이션, A/B/C 세트)을 수행하라. production.titles 필드를 JSON으로 출력하라."
        video_file = client.files.get(name=req.file_id)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[video_file, section_prompt], config={"response_mime_type": "application/json"})
        result_data = safe_parse_json(response.text)

        # 분석 결과 업데이트
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        last_res_path = os.path.join(persisted_temp_dir, "last_result.json")
        if os.path.exists(last_res_path):
            try:
                with open(last_res_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                # production 필드 업데이트
                if "production" not in old_data: old_data["production"] = {}
                if "titles" not in old_data["production"]: old_data["production"]["titles"] = {}
                old_data["production"]["titles"].update(result_data.get("production", {}).get("titles", {}))
                with open(last_res_path, "w", encoding="utf-8") as f:
                    json.dump(old_data, f, ensure_ascii=False)
            except: pass

        return {"step": 4, "status": "complete", "data": result_data, "message": "제목 생성 완료"}
    except Exception as e:
        return {"step": 4, "status": "error", "message": str(e)}

@app.post("/api/step/editpoints")
async def step_editpoints(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        video_file = client.files.get(name=req.file_id)
        full_prompt = load_prompt()
        section_prompt = full_prompt + "\n\n[이번 단계 지시] 대본: " + json.dumps(req.script_data, ensure_ascii=False) + "\n위 프로토콜 중 LAYER 5(6구간 편집 설계, 이탈 방지 장치, Edit Decision List)를 수행하라. edit_map, content_id_analysis, timeline_ratio 필드를 JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[video_file, section_prompt], config={"response_mime_type": "application/json"})
        result_data = safe_parse_json(response.text)

        # 분석 결과 업데이트
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        last_res_path = os.path.join(persisted_temp_dir, "last_result.json")
        if os.path.exists(last_res_path):
            try:
                with open(last_res_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                old_data.update(result_data)
                with open(last_res_path, "w", encoding="utf-8") as f:
                    json.dump(old_data, f, ensure_ascii=False)
            except: pass

        return {"step": 5, "status": "complete", "data": result_data, "message": "편집점 생성 완료"}
    except Exception as e:
        return {"step": 5, "status": "error", "message": str(e)}

@app.post("/api/step/variations")
async def step_variations(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        full_prompt = load_prompt()
        section_prompt = full_prompt + "\n\n[이번 단계 지시] 분석: " + json.dumps(req.analysis_data, ensure_ascii=False) + "\n대본: " + json.dumps(req.script_data, ensure_ascii=False) + "\n위 프로토콜 중 감정 변주 4종(물욕/본능/감동/분노)을 수행하라. emotional_variations 필드를 JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[section_prompt], config={"response_mime_type": "application/json"})
        result_data = safe_parse_json(response.text)

        # 분석 결과 업데이트
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        last_res_path = os.path.join(persisted_temp_dir, "last_result.json")
        if os.path.exists(last_res_path):
            try:
                with open(last_res_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                old_data.update(result_data)
                with open(last_res_path, "w", encoding="utf-8") as f:
                    json.dump(old_data, f, ensure_ascii=False)
            except: pass

        return {"step": 6, "status": "complete", "data": result_data, "message": "변주 대본 완료"}
    except Exception as e:
        return {"step": 6, "status": "error", "message": str(e)}

@app.post("/api/step/keywords")
async def step_keywords(req: StepRequest, x_api_key: str = Header(None)):
    try:
        client = get_client(x_api_key)
        full_prompt = load_prompt()
        section_prompt = full_prompt + "\n\n[이번 단계 지시] 분석: " + json.dumps(req.analysis_data, ensure_ascii=False) + "\n위 프로토콜 중 LAYER 6(한국어 25개 + 영어 25개 검색 키워드)을 수행하라. search_keywords 필드를 JSON으로 출력하라."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[section_prompt], config={"response_mime_type": "application/json"})
        result_data = safe_parse_json(response.text)

        # 분석 결과 업데이트
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        last_res_path = os.path.join(persisted_temp_dir, "last_result.json")
        if os.path.exists(last_res_path):
            try:
                with open(last_res_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                old_data.update(result_data)
                with open(last_res_path, "w", encoding="utf-8") as f:
                    json.dump(old_data, f, ensure_ascii=False)
            except: pass

        return {"step": 7, "status": "complete", "data": result_data, "message": "키워드 생성 완료"}
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
        
        if not prompt_content:
            prompt_content = "이 영상을 분석하고 JSON으로 출력하라."

        # JSON 스키마 강제 지시어 추가
        json_schema_instruction = """
⚠️ [필수] 응답 JSON 스키마 - 반드시 아래 키 이름을 정확히 사용하라. 한국어 키 금지. 이모지 키 금지.

```json
{
  "viral_dashboard": {
    "material_potential": "A~F",
    "material_potential_fulfilled_items": "N/7",
    "first_impression_power": "✅통과 또는 ❌재설계",
    "retention_gate": { "3_second_gate": "완료/미완료", "15_second_gate": "완료/미완료" },
    "rewatch_devices": "string",
    "loop_connection": "완성/미완성",
    "overall_grade": "S/A/B/C/D/F",
    "remediation_recommendation": "string or N/A"
  },
  "channel_safety": "🟢 안전 / 🟡 주의 / 🔴 위험",
  "revenue_risk": "🟢 광고 적합 / 🟡 제한 / 🔴 부적합",
  "target": {
    "anchor_target": { "name": "string", "identity": "string", "interests": "string", "tone": "string" },
    "sub_target": "string"
  },
  "deep_dive_report": {
    "what_it_is": "string",
    "principle": "string",
    "how_it_works": "string",
    "terminology": [ { "video_term": "string", "accurate_term": "string", "description": "string" } ],
    "why": "string",
    "pros_cons": { "pros": ["string"], "cons": ["string"] },
    "cost": "string",
    "duration": "string",
    "surprising_facts": ["string"],
    "expert_rebuttal_defense": [ { "criticism": "string", "defense": "string" } ]
  },
  "production": {
    "target_attractiveness_score": "N/10",
    "story_structure_model": "string",
    "emotion_curve": [ { "time": "0-3s", "emotion": "string", "intensity": 7 } ],
    "viral_titles": [ { "title": "string", "score": "N/20" } ],
    "final_script": "string (use \\n for line breaks)"
  },
  "edit_decision_list": [
    { "timecode": "00:00-00:03", "edit_event": "string", "script_sync": "string", "subtitle": "string", "audio": "string" }
  ],
  "search_keywords": [ { "korean": "string", "english": "string" } ],
  "optimization": "string",
  "thumbnails": []
}
```
viral_titles는 반드시 5개 이상 생성하라. 각 제목은 서로 다른 전략(호기심, 검색최적화, 감정자극, 반전, 공감)을 사용하라.
위 키 이름을 한 글자도 바꾸지 마라. 값만 채워라. """

        full_prompt = prompt_content + json_schema_instruction

        # Generate content
        print("Analyzing video content with Gemini 2.5 Flash...")
        print(f"Prompt length: {len(full_prompt)} chars")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[video_file, full_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=65536,
            )
        )

        # Parse Gemini response
        result_json = safe_parse_json(response.text)
        result_json = normalize_result(result_json)
        print(f"Analysis complete. Keys: {list(result_json.keys())}")

        # 분석 결과 저장 (render에서 사용)
        persisted_temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(persisted_temp_dir, exist_ok=True)
        with open(os.path.join(persisted_temp_dir, "last_result.json"), "w", encoding="utf-8") as f:
            json.dump(result_json, f, ensure_ascii=False)
            
        # 비디오 파일도 temp 폴더에 저장 (render에서 사용)
        persisted_video_path = os.path.join(persisted_temp_dir, f"last_video_{file.filename}")
        shutil.copy2(temp_file_path, persisted_video_path)

        # Extract thumbnails
        try:
            edit_list = result_json.get("edit_decision_list", []) or result_json.get("edit_map", {}).get("edit_decision_list", [])
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
async def render_video():
    """분석 결과 기반 자동 편집 영상 생성"""
    import json as json_module
    from editor.auto_editor import auto_edit
    
    # 가장 최근 업로드된 영상 찾기
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    video_path = None
    if os.path.exists(temp_dir):
        for f in sorted(os.listdir(temp_dir), reverse=True):
            if f.startswith("last_video_"):
                video_path = os.path.join(temp_dir, f)
                break
    
    if not video_path or not os.path.exists(video_path):
        return JSONResponse(status_code=400, content={"error": "영상 파일을 찾을 수 없습니다"})
    
    # 가장 최근 분석 결과 찾기
    result_path = os.path.join(temp_dir, "last_result.json")
    if not os.path.exists(result_path):
        return JSONResponse(status_code=400, content={"error": "분석 결과가 없습니다. 먼저 영상을 분석해주세요."})
    
    with open(result_path, "r", encoding="utf-8") as f:
        analysis_result = json_module.load(f)
    
    output_path = os.path.join(temp_dir, "edited_output.mp4")
    
    try:
        result_path_out = auto_edit(video_path, analysis_result, output_path)
        return FileResponse(
            result_path_out,
            media_type="video/mp4",
            filename="scenespark_edited.mp4"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/export/fcpxml")
async def export_fcpxml(data: dict):
    try:
        fcpxml_str = generate_fcpxml(data)
        return Response(content=fcpxml_str, media_type="application/xml", 
                        headers={"Content-Disposition": "attachment; filename=project.fcpxml"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/api/export/premiere")
async def export_premiere(data: dict):
    try:
        xml_str = generate_premiere_xml(data)
        return Response(content=xml_str, media_type="application/xml", 
                        headers={"Content-Disposition": "attachment; filename=project.xml"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/api/export/srt")
async def export_srt(data: dict):
    try:
        srt_str = generate_srt(data)
        return Response(content=srt_str, media_type="text/plain", 
                        headers={"Content-Disposition": "attachment; filename=subtitles.srt"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/api/export/zip")
async def export_zip(data: dict):
    try:
        fcp = generate_fcpxml(data)
        pre = generate_premiere_xml(data)
        srt = generate_srt(data)
        zip_bytes = create_export_zip(fcp, pre, srt)
        return Response(content=zip_bytes, media_type="application/zip", 
                        headers={"Content-Disposition": "attachment; filename=scene-spark-export.zip"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
