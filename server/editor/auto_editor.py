import subprocess
import json
import os
import tempfile
import shutil


def parse_timecode(tc: str) -> float:
    """'00:04~00:05' 또는 '00:00:04.000' 형태를 초 단위 float로 변환"""
    tc = tc.strip()
    if ":" in tc and tc.count(":") == 2:
        parts = tc.split(":")
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif ":" in tc:
        parts = tc.split(":")
        return float(parts[0]) * 60 + float(parts[1])
    return float(tc)


def parse_timecode_range(tc_range: str):
    """'00:04~00:05' -> (4.0, 5.0)"""
    parts = tc_range.split("~")
    return parse_timecode(parts[0]), parse_timecode(parts[1])


def detect_edit_effects(edit_event: str):
    """편집 이벤트 텍스트에서 효과 감지"""
    effects = {
        "zoom_in": False,
        "zoom_out": False,
        "slow_motion": False,
        "slow_factor": 1.0,
        "speed_up": False,
        "speed_factor": 1.0,
        "freeze": False,
        "freeze_duration": 0.0,
    }
    lower = edit_event.lower()
    if "줌인" in edit_event or "zoom" in lower and "in" in lower:
        effects["zoom_in"] = True
    if "줌아웃" in edit_event or "zoom" in lower and "out" in lower:
        effects["zoom_out"] = True
    if "슬로모션" in edit_event or "슬로우" in edit_event or "slow" in lower:
        effects["slow_motion"] = True
        # 배속 추출 (예: 0.7배속)
        import re
        match = re.search(r"(\d+\.?\d*)배속", edit_event)
        if match:
            effects["slow_factor"] = float(match.group(1))
        else:
            effects["slow_factor"] = 0.5
    if "배속" in edit_event and "슬로" not in edit_event and "slow" not in lower:
        import re
        match = re.search(r"(\d+\.?\d*)배속", edit_event)
        if match:
            val = float(match.group(1))
            if val > 1.0:
                effects["speed_up"] = True
                effects["speed_factor"] = val
    if "정지" in edit_event or "freeze" in lower:
        effects["freeze"] = True
        import re
        match = re.search(r"(\d+\.?\d*)초", edit_event)
        if match:
            effects["freeze_duration"] = float(match.group(1))
        else:
            effects["freeze_duration"] = 0.3
    return effects


def build_subtitle_ass(edl: list, video_width: int, video_height: int, title: str = "") -> str:
    """EDL에서 ASS 자막 파일 내용 생성"""
    header = f"""[Script Info]
Title: SceneSpark Auto Edit
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Arial,28,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,8,20,20,25,1
Style: Subtitle,Arial,22,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,20,20,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    
    # 상단 제목 고정 (전체 영상 길이)
    if title:
        last_edl = edl[-1] if edl else None
        if last_edl:
            _, end_time = parse_timecode_range(last_edl["timecode"])
        else:
            end_time = 60.0
        end_ts = format_ass_time(end_time)
        events.append(f"Dialogue: 0,0:00:00.00,{end_ts},Title,,0,0,0,,{title}")
    
    # 하단 자막
    for item in edl:
        sub = item.get("subtitle_text", "").strip()
        if not sub:
            continue
        start, end = parse_timecode_range(item["timecode"])
        start_ts = format_ass_time(start)
        end_ts = format_ass_time(end)
        events.append(f"Dialogue: 0,{start_ts},{end_ts},Subtitle,,0,0,0,,{sub}")
    
    return header + "\n".join(events)


def format_ass_time(seconds: float) -> str:
    """초를 ASS 타임스탬프 형식으로 변환 (H:MM:SS.CC)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def get_video_info(video_path: str) -> dict:
    """FFprobe로 영상 정보 추출"""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    video_stream = None
    for s in info.get("streams", []):
        if s["codec_type"] == "video":
            video_stream = s
            break
    return {
        "width": int(video_stream["width"]) if video_stream else 1080,
        "height": int(video_stream["height"]) if video_stream else 1920,
        "duration": float(info.get("format", {}).get("duration", 0)),
        "fps": eval(video_stream.get("r_frame_rate", "30/1")) if video_stream else 30,
    }


def auto_edit(video_path: str, analysis_result: dict, output_path: str = None) -> str:
    """
    분석 결과를 기반으로 자동 편집된 영상 생성
    
    Parameters:
        video_path: 원본 영상 경로
        analysis_result: Gemini 분석 결과 JSON
        output_path: 출력 경로 (None이면 자동 생성)
    
    Returns:
        출력 영상 경로
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "scenespark_output.mp4")
    
    work_dir = tempfile.mkdtemp(prefix="scenespark_")
    
    try:
        # 영상 정보
        vinfo = get_video_info(video_path)
        w, h = vinfo["width"], vinfo["height"]
        fps = vinfo["fps"]
        
        # EDL 추출
        edl = analysis_result.get("edit_map", {}).get("edit_decision_list", [])
        if not edl:
            raise ValueError("edit_decision_list가 비어있습니다")
        
        # 제목 추출
        title = ""
        vt = analysis_result.get("production", {}).get("viral_titles", {})
        if vt and vt.get("A_main", {}).get("title"):
            title = vt["A_main"]["title"]
        elif analysis_result.get("A_main", {}).get("title"):
            title = analysis_result["A_main"]["title"]
        
        # ASS 자막 생성
        ass_content = build_subtitle_ass(edl, w, h, title)
        ass_path = os.path.join(work_dir, "subtitles.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        
        # 세그먼트별 처리
        segment_files = []
        for idx, item in enumerate(edl):
            start, end = parse_timecode_range(item["timecode"])
            duration = end - start
            if duration <= 0:
                continue
            
            effects = detect_edit_effects(item.get("edit_event", ""))
            segment_path = os.path.join(work_dir, f"seg_{idx:03d}.mp4")
            
            # 필터 체인 구성
            filters = []
            
            # 줌인 효과
            if effects["zoom_in"]:
                filters.append(
                    f"zoompan=z='min(zoom+0.003,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration * fps)}:s={w}x{h}:fps={fps}"
                )
            # 줌아웃 효과
            elif effects["zoom_out"]:
                filters.append(
                    f"zoompan=z='if(eq(on,1),1.3,max(zoom-0.003,1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration * fps)}:s={w}x{h}:fps={fps}"
                )
            
            # 슬로모션
            speed_filter = ""
            atempo_filter = ""
            if effects["slow_motion"]:
                factor = effects["slow_factor"]
                speed_filter = f"setpts={1/factor}*PTS"
                if factor > 0:
                    atempo_filter = f"atempo={factor}"
            elif effects["speed_up"]:
                factor = effects["speed_factor"]
                speed_filter = f"setpts={1/factor}*PTS"
                if factor <= 2.0:
                    atempo_filter = f"atempo={factor}"
            
            if speed_filter:
                filters.append(speed_filter)
            
            # FFmpeg 명령어 구성
            vf = ",".join(filters) if filters else None
            
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start),
                "-t", str(duration),
                "-i", video_path,
            ]
            
            filter_complex_parts = []
            if vf:
                filter_complex_parts.append(f"[0:v]{vf}[vout]")
            if atempo_filter:
                filter_complex_parts.append(f"[0:a]{atempo_filter}[aout]")
            
            if filter_complex_parts:
                cmd += ["-filter_complex", ";".join(filter_complex_parts)]
                if vf:
                    cmd += ["-map", "[vout]"]
                else:
                    cmd += ["-map", "0:v"]
                if atempo_filter:
                    cmd += ["-map", "[aout]"]
                else:
                    cmd += ["-map", "0:a?"]
            else:
                cmd += ["-map", "0:v", "-map", "0:a?"]
            
            cmd += [
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                "-r", str(fps),
                segment_path
            ]
            
            subprocess.run(cmd, capture_output=True, text=True)
            
            if os.path.exists(segment_path):
                segment_files.append(segment_path)
        
        if not segment_files:
            raise ValueError("생성된 세그먼트가 없습니다")
        
        # concat 파일 생성
        concat_path = os.path.join(work_dir, "concat.txt")
        with open(concat_path, "w", encoding="utf-8") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")
        
        # 세그먼트 합치기
        merged_path = os.path.join(work_dir, "merged.mp4")
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_path,
            "-c", "copy",
            merged_path
        ]
        subprocess.run(cmd_concat, capture_output=True, text=True)
        
        # 자막 합성 (ASS burn-in)
        ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
        cmd_sub = [
            "ffmpeg", "-y",
            "-i", merged_path,
            "-vf", f"ass='{ass_escaped}'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "copy",
            output_path
        ]
        subprocess.run(cmd_sub, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            # 자막 합성 실패 시 merged 파일을 그대로 사용
            shutil.copy2(merged_path, output_path)
        
        return output_path
    
    finally:
        # 임시 파일 정리
        try:
            shutil.rmtree(work_dir)
        except:
            pass
