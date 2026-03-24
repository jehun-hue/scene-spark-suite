import subprocess
import os
import base64
from pathlib import Path

def extract_thumbnails(video_path: str, timecodes: list[str], output_dir: str) -> list[dict]:
    """
    영상에서 타임코드별 썸네일을 추출한다.
    timecodes: ["00:00:00.000", "00:00:15.000", ...] 형태
    반환: [{"timecode": "00:00:00.000", "thumbnail_base64": "data:image/jpeg;base64,..."}, ...]
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    for i, tc in enumerate(timecodes):
        output_path = os.path.join(output_dir, f"thumb_{i:03d}.jpg")
        cmd = [
            "ffmpeg", "-y",
            "-ss", tc,
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "5",
            "-vf", "scale=160:90",
            output_path
        ]
        try:
            # Check if ffmpeg is available first
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            
            subprocess.run(cmd, capture_output=True, timeout=10)
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                results.append({
                    "timecode": tc,
                    "thumbnail_base64": f"data:image/jpeg;base64,{b64}"
                })
            else:
                results.append({"timecode": tc, "thumbnail_base64": None})
        except (subprocess.SubprocessError, FileNotFoundError):
            # ffmpeg not found or error
            results.append({"timecode": tc, "thumbnail_base64": None})
        except Exception:
            results.append({"timecode": tc, "thumbnail_base64": None})
    
    return results
