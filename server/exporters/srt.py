from datetime import timedelta

def generate_srt(analysis_json: dict) -> str:
    """Generates SubRip Text (SRT) format for analysis script."""
    edit_list = analysis_json.get("edit_map", {}).get("edit_decision_list", [])
    srt_lines = []
    
    current_time = timedelta(seconds=0)
    for idx, item in enumerate(edit_list):
        subtitle = item.get("subtitle_text", "")
        if not subtitle: continue
        
        # Duration: assume 3 seconds for simplicity unless timecode available
        duration = timedelta(seconds=3)
        end_time = current_time + duration
        
        start_str = format_srt_time(current_time)
        end_str = format_srt_time(end_time)
        
        srt_lines.append(f"{idx + 1}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(f"{subtitle}\n")
        
        current_time = end_time
        
    return "\n".join(srt_lines)

def format_srt_time(td: timedelta) -> str:
    """Format timedelta to SRT HH:MM:SS,mmm."""
    ms = td.microseconds // 1000
    sec = td.seconds % 60
    min = (td.seconds // 60) % 60
    hour = (td.seconds // 3600)
    return f"{hour:02d}:{min:02d}:{sec:02d},{ms:03d}"
