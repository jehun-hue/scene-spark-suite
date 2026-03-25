import xml.etree.ElementTree as ET

def generate_premiere_xml(analysis_json: dict, video_filename: str = 'source.mp4') -> str:
    edit_list = analysis_json.get('edit_decision_list', []) or analysis_json.get('edit_map', {}).get('edit_decision_list', [])
    xmeml = ET.Element('xmeml', version='4')
    sequence = ET.SubElement(xmeml, 'sequence', id='Sequence 1')
    ET.SubElement(sequence, 'name').text = 'Scene Spark Export'
    ET.SubElement(sequence, 'duration').text = '0'
    rate = ET.SubElement(sequence, 'rate')
    ET.SubElement(rate, 'timebase').text = '30'
    ET.SubElement(rate, 'ntsc').text = 'FALSE'
    media = ET.SubElement(sequence, 'media')
    video = ET.SubElement(media, 'video')
    track = ET.SubElement(video, 'track')
    for idx, item in enumerate(edit_list):
        clipitem = ET.SubElement(track, 'clipitem', id=f'clip-{idx}')
        ET.SubElement(clipitem, 'name').text = (item.get('subtitle') or item.get('subtitle_text') or item.get('caption') or 'Clip')
        ET.SubElement(clipitem, 'duration').text = '90'
        ET.SubElement(clipitem, 'start').text = str(idx * 90)
        ET.SubElement(clipitem, 'end').text = str((idx + 1) * 90)
        file_el = ET.SubElement(clipitem, 'file', id=f'file-{idx}')
        ET.SubElement(file_el, 'name').text = video_filename
        ET.SubElement(file_el, 'pathurl').text = f'file://localhost/{video_filename}'
    return '<?xml version=1.0 encoding=UTF-8?>\n' + ET.tostring(xmeml, encoding='unicode', method='xml')
