from datetime import timedelta

def generate_srt(analysis_json: dict) -> str:
    edit_list = analysis_json.get('edit_decision_list', []) or analysis_json.get('edit_map', {}).get('edit_decision_list', [])
    srt_lines = []
    current_time = timedelta(seconds=0)
    for idx, item in enumerate(edit_list):
        subtitle = (item.get('subtitle') or item.get('subtitle_text') or item.get('caption') or '')
        if not subtitle:
            continue
        duration = timedelta(seconds=3)
        end_time = current_time + duration
        start_str = format_srt_time(current_time)
        end_str = format_srt_time(end_time)
        srt_lines.append(f'{idx + 1}')
        srt_lines.append(f'{start_str} --> {end_str}')
        srt_lines.append(f'{subtitle}\n')
        current_time = end_time
    return '\n'.join(srt_lines)

def format_srt_time(td: timedelta) -> str:
    ms = td.microseconds // 1000
    sec = td.seconds % 60
    min = (td.seconds // 60) % 60
    hour = (td.seconds // 3600)
    return f'{hour:02d}:{min:02d}:{sec:02d},{ms:03d}'
