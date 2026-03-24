import subprocess
import os
import shutil
import json
from pathlib import Path

def cut_segments(video_path: str, segments: list[dict], output_dir: str) -> list[str]:
    """Cut video into segments based on start/end/speed."""
    os.makedirs(output_dir, exist_ok=True)
    out_paths = []
    
    for i, seg in enumerate(segments):
        start = seg.get("start", "00:00:00.000")
        end = seg.get("end", "00:00:03.000")
        speed = seg.get("speed", 1.0)
        
        # Calculate duration
        start_ts = timestamp_to_seconds(start)
        end_ts = timestamp_to_seconds(end)
        duration = end_ts - start_ts
        
        out_path = os.path.join(output_dir, f"segment_{i:03d}.mp4")
        
        # Filter: speed adjustment
        # setpts=1/speed*PTS for video, atempo=speed for audio
        filters = []
        if speed != 1.0:
            filters.append(f"setpts={1.0/speed}*PTS")
            # Note: atempo only supports 0.5 to 2.0. If outside, need chaining.
            afilt = f"atempo={speed}"
            cmd = [
                "ffmpeg", "-y",
                "-ss", start,
                "-t", str(duration),
                "-i", video_path,
                "-vf", ",".join(filters),
                "-af", afilt,
                "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                out_path
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-ss", start,
                "-t", str(duration),
                "-i", video_path,
                "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                out_path
            ]
            
        subprocess.run(cmd, capture_output=True, check=True)
        out_paths.append(out_path)
        
    return out_paths

def apply_zoom(video_path: str, zoom_level: float, output_path: str) -> str:
    """Apply a static zoom effect."""
    # Simple static zoom using scale and crop
    # zoom_level 1.5 -> scale by 1.5 then crop original size from center
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"scale=iw*{zoom_level}:-1,crop=iw/{zoom_level}:ih/{zoom_level}",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path

def reframe_vertical(video_path: str, output_path: str) -> str:
    """9:16 vertical reframe."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "crop=ih*9/16:ih,scale=1080:1920",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path

def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> str:
    """Hardcode subtitles."""
    # Escape path for ffmpeg subtitles filter (especially on Windows)
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles='{escaped_srt}':force_style='FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Alignment=2'",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path

def concat_videos(video_paths: list[str], output_path: str) -> str:
    """Concatenate multiple videos into one."""
    list_path = "concat_list.txt"
    with open(list_path, "w") as f:
        for p in video_paths:
            # Full absolute path for safety
            abs_p = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")
            
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    os.remove(list_path)
    return output_path

def timestamp_to_seconds(ts: str) -> float:
    """Helper to convert HH:MM:SS.mmm to seconds."""
    h, m, s = ts.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def render_final_short(video_path: str, analysis_json: dict, output_path: str, vertical: bool = True) -> str:
    """Main rendering pipeline."""
    work_dir = "render_work"
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    
    try:
        # 1. Extract segments
        edit_list = analysis_json.get("edit_map", {}).get("edit_decision_list", [])
        segments = []
        for i, item in enumerate(edit_list):
            start = item.get("timecode", "00:00:00.000")
            # For simplicity, assume 3s duration if not provided
            start_s = timestamp_to_seconds(start)
            end_s = start_s + 3.0
            end = f"{int(end_s//3600):02d}:{int((end_s//60)%60):02d}:{end_s%60:06.3f}"
            segments.append({
                "start": start,
                "end": end,
                "speed": 1.0,
                "zoom": 1.2 if i % 3 == 0 else 1.0 # Example: zoom every 3rd clip
            })
            
        # 2. Cut
        cut_dir = os.path.join(work_dir, "cuts")
        seg_paths = cut_segments(video_path, segments, cut_dir)
        
        # 3. Apply Zoom
        processed_segs = []
        for i, (p, seg) in enumerate(zip(seg_paths, segments)):
            if seg.get("zoom", 1.0) > 1.0:
                zp = os.path.join(work_dir, f"zoom_{i:03d}.mp4")
                apply_zoom(p, seg["zoom"], zp)
                processed_segs.append(zp)
            else:
                processed_segs.append(p)
                
        # 4. Concat
        merged_path = os.path.join(work_dir, "merged.mp4")
        concat_videos(processed_segs, merged_path)
        
        # 5. Subtitles
        # Generate temporary SRT
        srt_path = os.path.join(work_dir, "temp.srt")
        srt_content = []
        curr = 0.0
        for i, item in enumerate(edit_list):
            start = curr
            end = curr + 3.0
            text = item.get("subtitle_text", "")
            srt_content.append(f"{i+1}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{text}\n")
            curr = end
            
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))
            
        subbed_path = os.path.join(work_dir, "subbed.mp4")
        burn_subtitles(merged_path, srt_path, subbed_path)
        
        # 6. Reframe
        if vertical:
            reframe_vertical(subbed_path, output_path)
        else:
            shutil.copy(subbed_path, output_path)
            
        return output_path
        
    finally:
        # Cleanup
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

def format_srt_time(seconds: float) -> str:
    td_ms = int((seconds % 1) * 1000)
    td_sec = int(seconds % 60)
    td_min = int((seconds // 60) % 60)
    td_hr = int(seconds // 3600)
    return f"{td_hr:02d}:{td_min:02d}:{td_sec:02d},{td_ms:03d}"
