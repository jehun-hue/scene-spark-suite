import io
import zipfile
import os
import json

def create_export_zip(fcpxml: str, video_path: str = None, analysis_json: dict = None) -> bytes:
    """Creates a ZIP archive containing all export files in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("project.fcpxml", fcpxml)
        
        if video_path and os.path.exists(video_path):
            z.write(video_path, arcname=os.path.basename(video_path))
            
        if analysis_json:
            z.writestr("analysis_result.json", json.dumps(analysis_json, ensure_ascii=False, indent=2))
    
    buf.seek(0)
    return buf.getvalue()
