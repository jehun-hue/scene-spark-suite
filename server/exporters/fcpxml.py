import xml.etree.ElementTree as ET
import re

def _tc_to_seconds(tc: str) -> float:
    tc = tc.strip()
    if tc.count(':') == 2:
        parts = tc.split(':')
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif tc.count(':') == 1:
        parts = tc.split(':')
        return float(parts[0]) * 60 + float(parts[1])
    return float(tc)

def _parse_range(tc_range: str):
    if '~' in tc_range:
        parts = tc_range.split('~')
        return _tc_to_seconds(parts[0]), _tc_to_seconds(parts[1])
    m = re.match(r'^(\d+:\d+(?::\d+)?(?:\.\d+)?)\s*-\s*(\d+:\d+(?::\d+)?(?:\.\d+)?)$', tc_range.strip())
    if m:
        return _tc_to_seconds(m.group(1)), _tc_to_seconds(m.group(2))
    parts = tc_range.split('-')
    return _tc_to_seconds(parts[0]), _tc_to_seconds(parts[-1])

def _seconds_to_rational(s: float, fps: int = 30) -> str:
    frames = round(s * fps)
    return f'{frames}/{fps}s'

def _detect_effects(edit_event: str) -> dict:
    effects = {'zoom_in': False, 'zoom_out': False, 'slow': False, 'slow_factor': 1.0, 'speed_factor': 1.0}
    lower = edit_event.lower()
    if 'zoom' in lower and 'in' in lower:
        effects['zoom_in'] = True
    if 'zoom' in lower and 'out' in lower:
        effects['zoom_out'] = True
    if 'slow' in lower:
        effects['slow'] = True
        effects['slow_factor'] = 0.5
    return effects

def generate_fcpxml(analysis_json: dict, video_filename: str = 'source.mp4', fps: int = 30) -> str:
    edl = (analysis_json.get('edit_decision_list')
           or analysis_json.get('edit_map', {}).get('edit_decision_list')
           or analysis_json.get('edit_engineering', {}).get('edit_decision_list')
           or [])
    if not edl:
        raise ValueError('edit_decision_list is empty')
    title_text = ''
    vt = (analysis_json.get('production', {}).get('viral_titles')
          or analysis_json.get('viral_titles') or [])
    if isinstance(vt, list) and len(vt) > 0:
        first = vt[0]
        title_text = first.get('title', '') if isinstance(first, dict) else str(first)
    elif isinstance(vt, dict) and vt.get('A_main', {}).get('title'):
        title_text = vt['A_main']['title']
    last_start, last_end = _parse_range(edl[-1]['timecode'])
    total_duration = last_end
    total_dur_rat = _seconds_to_rational(total_duration, fps)
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE fcpxml>')
    lines.append('<fcpxml version="1.11">')
    lines.append('  <resources>')
    lines.append(f'    <format id="r0" name="FFVideoFormat1080p{fps}" frameDuration="{_seconds_to_rational(1.0/fps, fps)}" width="1920" height="1080"/>')
    lines.append(f'    <asset id="r1" name="{video_filename}" duration="{total_dur_rat}" hasVideo="1" hasAudio="1" format="r0">')
    lines.append(f'      <media-rep kind="original-media" src="{video_filename}"/>')
    lines.append('    </asset>')
    lines.append('    <effect id="r2" name="Basic Title" uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"/>')
    lines.append('  </resources>')
    lines.append('  <library>')
    lines.append('    <event name="SceneSpark Export">')
    lines.append('      <project name="SceneSpark Auto Edit">')
    lines.append(f'        <sequence format="r0" duration="{total_dur_rat}" tcStart="0/1s" tcFormat="NDF">')
    lines.append('          <spine>')
    for idx, item in enumerate(edl):
        start, end = _parse_range(item['timecode'])
        clip_dur = end - start
        if clip_dur <= 0:
            continue
        effects = _detect_effects(item.get('edit_event', ''))
        subtitle = (item.get('subtitle') or item.get('subtitle_text') or item.get('caption') or '').strip()
        offset_rat = _seconds_to_rational(start, fps)
        start_rat = _seconds_to_rational(start, fps)
        dur_rat = _seconds_to_rational(clip_dur, fps)
        clip_name = item.get('edit_event', f'Clip {idx+1}').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(f'          <clip name="{clip_name}" offset="{offset_rat}" duration="{dur_rat}" start="{start_rat}" format="r0">')
        lines.append(f'            <video ref="r1" offset="{start_rat}" duration="{dur_rat}"/>')
        if subtitle:
            sub_esc = subtitle.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            ts_id = f"ts{idx+1}"
            lines.append(f'            <title ref="r2" name="{sub_esc}" offset="0/1s" duration="{dur_rat}" start="3600/1s">')
            lines.append(f'              <text><text-style ref="{ts_id}">{sub_esc}</text-style></text>')
            lines.append(f'              <text-style-def id="{ts_id}"><text-style font="Arial" fontSize="42" fontColor="1 1 1 1" bold="1"/></text-style-def>')
            lines.append('            </title>')
        lines.append('          </clip>')
    if title_text:
        t_esc = title_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(f'          <title ref="r2" name="{t_esc}" lane="1" offset="0/1s" duration="{total_dur_rat}" start="3600/1s">')
        lines.append(f'            <text><text-style ref="ts_title">{t_esc}</text-style></text>')
        lines.append('            <text-style-def id="ts_title"><text-style font="Arial" fontSize="36" fontColor="1 1 0.2 1" bold="1"/></text-style-def>')
        lines.append('          </title>')
    lines.append('          </spine>')
    lines.append('        </sequence>')
    lines.append('      </project>')
    lines.append('    </event>')
    lines.append('  </library>')
    lines.append('</fcpxml>')
    return chr(10).join(lines)
