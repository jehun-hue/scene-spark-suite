import xml.etree.ElementTree as ET
import re


def _tc_to_seconds(tc: str) -> float:
    """타임코드 문자열을 초 단위로 변환"""
    tc = tc.strip()
    if tc.count(":") == 2:
        parts = tc.split(":")
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif tc.count(":") == 1:
        parts = tc.split(":")
        return float(parts[0]) * 60 + float(parts[1])
    return float(tc)


def _parse_range(tc_range: str):
    """'00:04~00:05' -> (4.0, 5.0)"""
    parts = tc_range.split("~")
    return _tc_to_seconds(parts[0]), _tc_to_seconds(parts[1])


def _seconds_to_rational(s: float, fps: int = 30) -> str:
    """초를 FCPXML rational time으로 변환 (예: '120/30s')"""
    frames = round(s * fps)
    return f"{frames}/{fps}s"


def _detect_effects(edit_event: str) -> dict:
    """편집 이벤트에서 효과 감지"""
    effects = {"zoom_in": False, "zoom_out": False, "slow": False, "slow_factor": 1.0, "speed_factor": 1.0}
    lower = edit_event.lower()
    if "줌인" in edit_event or ("zoom" in lower and "in" in lower):
        effects["zoom_in"] = True
    if "줌아웃" in edit_event or ("zoom" in lower and "out" in lower):
        effects["zoom_out"] = True
    if "슬로모션" in edit_event or "슬로우" in edit_event or "slow" in lower:
        effects["slow"] = True
        match = re.search(r"(\d+\.?\d*)배속", edit_event)
        effects["slow_factor"] = float(match.group(1)) if match else 0.5
    if "배속" in edit_event and "슬로" not in edit_event:
        match = re.search(r"(\d+\.?\d*)배속", edit_event)
        if match:
            val = float(match.group(1))
            if val > 1.0:
                effects["speed_factor"] = val
    return effects


def generate_fcpxml(analysis_json: dict, video_filename: str = "source.mp4", fps: int = 30) -> str:
    """
    분석 결과를 기반으로 FCPXML 1.11 생성
    - 편집점별 컷 편집
    - 줌인/줌아웃 (Transform)
    - 슬로모션 (Retime)
    - 하단 자막
    - 상단 제목 고정
    """
    edl = (analysis_json.get("edit_decision_list")
           or analysis_json.get("edit_map", {}).get("edit_decision_list")
           or analysis_json.get("edit_engineering", {}).get("edit_decision_list")
           or analysis_json.get("edit_engineering", {}).get("edl")
           or [])
    if not edl:
        raise ValueError("edit_decision_list가 비어있습니다")

    # 제목 추출
    title_text = ""
    vt = (analysis_json.get("production", {}).get("viral_titles")
          or analysis_json.get("viral_titles")
          or [])
    if isinstance(vt, list) and len(vt) > 0:
        first = vt[0]
        title_text = first.get("title", "") if isinstance(first, dict) else str(first)
    elif isinstance(vt, dict):
        if vt.get("A_main", {}).get("title"):
            title_text = vt["A_main"]["title"]

    # 전체 영상 길이 계산
    last_start, last_end = _parse_range(edl[-1]["timecode"])
    total_duration = last_end
    total_dur_rat = _seconds_to_rational(total_duration, fps)

    # XML 구조 시작
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE fcpxml>')
    lines.append('<fcpxml version="1.11">')
    lines.append('  <resources>')
    lines.append(f'    <format id="r0" name="FFVideoFormat1080p{fps}" frameDuration="{_seconds_to_rational(1.0/fps, fps)}" width="1920" height="1080"/>')
    lines.append(f'    <asset id="r1" name="{video_filename}" hasVideo="1" hasAudio="1" format="r0">')
    lines.append(f'      <media-rep kind="original-media" src="file:///localhost/{video_filename}"/>')
    lines.append('    </asset>')
    # 제목용 effect
    lines.append('    <effect id="r2" name="Basic Title" uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"/>')
    lines.append('  </resources>')
    lines.append('  <library>')
    lines.append('    <event name="SceneSpark Export">')
    lines.append('      <project name="SceneSpark Auto Edit">')
    lines.append(f'        <sequence format="r0" duration="{total_dur_rat}" tcStart="0/1s" tcFormat="NDF">')
    lines.append('          <spine>')

    # 각 편집점을 clip으로
    for idx, item in enumerate(edl):
        start, end = _parse_range(item["timecode"])
        clip_dur = end - start
        if clip_dur <= 0:
            continue

        effects = _detect_effects(item.get("edit_event", ""))
        subtitle = (item.get("subtitle") or item.get("subtitle_text") or item.get("자막") or item.get("caption") or "").strip()

        offset_rat = _seconds_to_rational(start, fps)
        start_rat = _seconds_to_rational(start, fps)
        dur_rat = _seconds_to_rational(clip_dur, fps)

        clip_name = item.get("source_segment", item.get("edit_event", f"Clip {idx+1}"))
        clip_name = clip_name.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;') if '&' not in clip_name else clip_name

        # 슬로모션/배속 적용
        if effects["slow"]:
            retime_dur = _seconds_to_rational(clip_dur / effects["slow_factor"], fps)
            lines.append(f'          <clip name="{clip_name}" offset="{offset_rat}" duration="{retime_dur}" start="{start_rat}" format="r0">')
            lines.append(f'            <video ref="r1" offset="{start_rat}" duration="{dur_rat}">')
            # Retime
            rate_val = effects["slow_factor"]
            lines.append(f'              <adjust-conform type="retime" amount="{rate_val}"/>')
        elif effects["speed_factor"] > 1.0:
            retime_dur = _seconds_to_rational(clip_dur / effects["speed_factor"], fps)
            lines.append(f'          <clip name="{clip_name}" offset="{offset_rat}" duration="{retime_dur}" start="{start_rat}" format="r0">')
            lines.append(f'            <video ref="r1" offset="{start_rat}" duration="{dur_rat}">')
            rate_val = effects["speed_factor"]
            lines.append(f'              <adjust-conform type="retime" amount="{rate_val}"/>')
        else:
            lines.append(f'          <clip name="{clip_name}" offset="{offset_rat}" duration="{dur_rat}" start="{start_rat}" format="r0">')
            lines.append(f'            <video ref="r1" offset="{start_rat}" duration="{dur_rat}">')

        # 줌인 효과 (Transform: scale 100% -> 130%)
        if effects["zoom_in"]:
            lines.append('              <adjust-transform>')
            lines.append('                <param name="scale">')
            lines.append(f'                  <keyframe time="0/1s" value="1 1"/>')
            lines.append(f'                  <keyframe time="{dur_rat}" value="1.3 1.3"/>')
            lines.append('                </param>')
            lines.append('              </adjust-transform>')
        elif effects["zoom_out"]:
            lines.append('              <adjust-transform>')
            lines.append('                <param name="scale">')
            lines.append(f'                  <keyframe time="0/1s" value="1.3 1.3"/>')
            lines.append(f'                  <keyframe time="{dur_rat}" value="1 1"/>')
            lines.append('                </param>')
            lines.append('              </adjust-transform>')

        lines.append('            </video>')

        # 하단 자막
        if subtitle:
            sub_escaped = subtitle.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            lines.append(f'            <title ref="r2" name="{sub_escaped}" offset="0/1s" duration="{dur_rat}" start="3600/1s">')
            lines.append('              <param name="Position" key="9999/999166631/999166633/1/100/101" value="0 -420"/>')
            lines.append('              <param name="Alignment" key="9999/999166631/999166633/2/354/999169573/401" value="1 (Center)"/>')
            lines.append(f'              <text><text-style ref="ts1">{sub_escaped}</text-style></text>')
            lines.append('              <text-style-def id="ts1">')
            lines.append('                <text-style font="Arial" fontSize="42" fontColor="1 1 1 1" bold="1" shadowColor="0 0 0 0.75" shadowOffset="2 315" alignment="center"/>')
            lines.append('              </text-style-def>')
            lines.append('            </title>')

        lines.append('          </clip>')

    # 상단 제목 고정 (spine 위에 lane 1으로)
    if title_text:
        title_escaped = title_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(f'          <title ref="r2" name="{title_escaped}" lane="1" offset="0/1s" duration="{total_dur_rat}" start="3600/1s">')
        lines.append('            <param name="Position" key="9999/999166631/999166633/1/100/101" value="0 440"/>')
        lines.append('            <param name="Alignment" key="9999/999166631/999166633/2/354/999169573/401" value="1 (Center)"/>')
        lines.append(f'            <text><text-style ref="ts2">{title_escaped}</text-style></text>')
        lines.append('            <text-style-def id="ts2">')
        lines.append('              <text-style font="Arial" fontSize="36" fontColor="1 1 0.2 1" bold="1" shadowColor="0 0 0 0.75" shadowOffset="2 315" alignment="center"/>')
        lines.append('            </text-style-def>')
        lines.append('          </title>')

    lines.append('          </spine>')
    lines.append('        </sequence>')
    lines.append('      </project>')
    lines.append('    </event>')
    lines.append('  </library>')
    lines.append('</fcpxml>')

    return "\n".join(lines)
