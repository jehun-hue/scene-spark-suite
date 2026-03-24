import io
import zipfile

def create_export_zip(fcpxml: str, premiere_xml: str, srt: str) -> bytes:
    """Creates a ZIP archive containing all export files in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("project.fcpxml", fcpxml)
        z.writestr("project.xml", premiere_xml)
        z.writestr("subtitles.srt", srt)
    
    buf.seek(0)
    return buf.getvalue()
