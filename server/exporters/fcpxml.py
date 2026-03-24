import xml.etree.ElementTree as ET
from datetime import timedelta

def generate_fcpxml(analysis_json: dict, video_filename: str = "source.mp4") -> str:
    """Generates FCPXML 1.11 for the analysis result."""
    edit_list = analysis_json.get("edit_map", {}).get("edit_decision_list", [])
    
    root = ET.Element("fcpxml", version="1.11")
    resources = ET.SubElement(root, "resources")
    asset = ET.SubElement(resources, "asset", id="r1", name=video_filename, src=f"file:///localhost/{video_filename}")
    
    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", name="Analysis Export")
    project = ET.SubElement(event, "project", name="Scene Spark Suite Project")
    sequence = ET.SubElement(project, "sequence", format="r1", duration="0s", tcStart="0s")
    spine = ET.SubElement(sequence, "spine")
    
    current_offset = 0.0
    for idx, item in enumerate(edit_list):
        # Extract time and convert to seconds if needed
        timecode = item.get("timecode", "00:00:00.000")
        subtitle = item.get("subtitle_text", "")
        
        # Simple duration estimation (e.g. 3s per clip if not specified)
        duration = 3.0 
        
        clip = ET.SubElement(spine, "asset-clip", 
                           ref="r1", 
                           offset=f"{current_offset}s", 
                           name=item.get("edit_event", "Clip"), 
                           start=f"{current_offset}s", 
                           duration=f"{duration}s")
        
        if subtitle:
            title = ET.SubElement(clip, "title", name=subtitle, offset="0s", duration=f"{duration}s")
            text = ET.SubElement(title, "text")
            text_style = ET.SubElement(text, "text-style", ref="ts1")
            text_style.text = subtitle
            
        current_offset += duration

    return ET.tostring(root, encoding="unicode", method="xml")
