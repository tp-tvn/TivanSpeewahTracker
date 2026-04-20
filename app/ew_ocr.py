"""
ew_ocr.py — Earthworks PLOD extraction via Claude Vision API.

Takes a PDF or image file, sends each page to Claude, and returns a structured
dict with extracted fields plus a 'flags' list for anything ambiguous or unclear.
Each flag includes bounding box coordinates so the UI can render a cropped snippet
of the exact value in question.
"""
import base64
import io
import json
import re
from pathlib import Path

_EXTRACTION_PROMPT = """
You are extracting data from a handwritten "Project Log of Daily Work - Earthworks" form
submitted by MDM Earthworks for the Speewah Fluorite Project.

The form has two pages:

PAGE 1:
- Header: Supervisor, Crew/Contractor, Works Description, Location, Date, Start Time, End Time, Area
- Mobilisation table (equipment + qty) and Demobilisation table (equipment + qty)
  Equipment names: D9 Dozer, D7 Dozer, 336 Excavator, 18.5t Wheeled Excavator,
                   16H Grader, Mitsubishi Fuso Tipper
- Equipment hours table:
  Rows: D9, D7, 16H Gdr, Tip Truck, Wheel Exc, 336 Exc, Service Truck, Survey Trailer
  Columns: Active Time (decimal hours), Standdown (decimal hours),
           Breakdown (decimal hours), Total Hours, Additional Notes
  NOTE: The 16H Grader row sometimes shows an hourmeter/odometer reading (a 5-digit number
        like "56425.7") instead of active hours. If you see a 5-digit number in the
        Active Time column treat it as hourmeter_end, not active_hours.
- Production table at bottom:
  Roads (km), Tracks (km), Pads (#), Sumps/Pits (#), Additional Notes

PAGE 2:
- Miscellaneous items table: item name, quantity, additional notes
  Rows include: Project Manager/Engineer, Superintendent, HSE, Admin,
                Fitter, MDM Commercial travel, Service Truck & supervisor,
                Drone Multi-Rotor, Base Station Trailer, Engineering Surveyor,
                Surveyor technician, Surveyor Commercial air travel
- Additional Comments section (free text)
- Contractor signature block: Name, Role
- Principal signature block: Name, Role

EXTRACTION RULES:
1. Return ONLY valid JSON — no prose before or after.
2. Dates: convert to YYYY-MM-DD format.
3. Times: convert to HH:MM (24hr) format.
4. Hours: extract as decimal numbers (e.g. "8.5", not "8hrs 30min").
   A dash "—" or blank means null, NOT zero.
5. Quantities in misc table: extract as string (may be hours like "12hrs" or a count like "2").
6. For each equipment row, also try to capture hourmeter_start and hourmeter_end if visible
   (these are 5-digit numbers, sometimes on a separate line or small text).
7. Use null for any field that is blank, a dash, or illegible.
8. The 'flags' array must include an entry for EVERY field where:
   - Handwriting is unclear or ambiguous
   - A value seems physically impossible (e.g. active + standdown > 14 hours)
   - You had to make an inference
   - A value is present but you are less than 90% confident in your reading

   Each flag MUST include a bounding box so the reviewer can see the exact region:
   - "page": 1 or 2 (which page of the form the value appears on)
   - "bbox_pct": [x, y, width, height] all as fractions 0.0–1.0 of that page's dimensions.
     x=0,y=0 is top-left. Be as precise as possible — tight around the handwritten value,
     not the whole row. Allow ~2% margin on each side.

Return this exact JSON structure:
{
  "date": "YYYY-MM-DD or null",
  "supervisor": "string or null",
  "contractor": "string or null",
  "works_description": "string or null",
  "location": "string or null",
  "area": "string or null",
  "start_time": "HH:MM or null",
  "end_time": "HH:MM or null",
  "mobilisations": [
    {"equipment": "name", "qty": number_or_null, "notes": "string or null"}
  ],
  "demobilisations": [
    {"equipment": "name", "qty": number_or_null, "notes": "string or null"}
  ],
  "equipment": [
    {
      "name": "equipment name as written",
      "active_hours": number_or_null,
      "standdown_hours": number_or_null,
      "breakdown_hours": number_or_null,
      "total_hours": number_or_null,
      "hourmeter_start": number_or_null,
      "hourmeter_end": number_or_null,
      "notes": "string or null"
    }
  ],
  "production": {
    "roads_km": number_or_null,
    "tracks_km": number_or_null,
    "pads_count": integer_or_null,
    "sumps_pits": integer_or_null,
    "notes": "string or null"
  },
  "misc": [
    {"item_name": "string", "quantity": "string or null", "notes": "string or null"}
  ],
  "additional_comments": "string or null",
  "principal_name": "string or null",
  "flags": [
    {
      "field": "dotted.path",
      "confidence": 0.0,
      "issue": "plain english description of the ambiguity",
      "page": 1,
      "bbox_pct": [x, y, width, height]
    }
  ]
}
"""


def _encode_file(path: Path) -> list[dict]:
    """
    Convert a PDF or image file into Anthropic content blocks.
    """
    suffix = path.suffix.lower()
    data = path.read_bytes()
    b64 = base64.standard_b64encode(data).decode("utf-8")

    if suffix == ".pdf":
        return [{
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": b64,
            },
        }]
    else:
        media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                     ".png": "image/png",  ".webp": "image/webp"}
        media_type = media_map.get(suffix, "image/jpeg")
        return [{
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64,
            },
        }]


def get_flag_snippet(file_bytes: bytes, filename: str, flag: dict,
                     padding: float = 0.025) -> tuple[bytes | None, str | None]:
    """
    Render a cropped image snippet for a flagged field.

    Uses pymupdf for PDFs and Pillow for images.

    Returns:
        (png_bytes, error_msg) — png_bytes is None on failure, error_msg explains why.
    """
    bbox = flag.get("bbox_pct")
    if not bbox or len(bbox) < 4:
        return None, "No bounding box coordinates returned by extraction"

    if not file_bytes:
        return None, "Source file bytes not available in session"

    x_pct, y_pct, w_pct, h_pct = [float(v) for v in bbox]
    page_num = max(0, int(flag.get("page", 1)) - 1)

    # Expand by padding, clamped to [0, 1]
    x1 = max(0.0, x_pct - padding)
    y1 = max(0.0, y_pct - padding)
    x2 = min(1.0, x_pct + w_pct + padding)
    y2 = min(1.0, y_pct + h_pct + padding)

    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        try:
            import fitz  # pymupdf
        except ImportError:
            return None, "pymupdf not installed — run: pip install pymupdf"
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page_num = min(page_num, len(doc) - 1)
            page = doc[page_num]
            r = page.rect
            clip = fitz.Rect(
                r.x0 + x1 * r.width,
                r.y0 + y1 * r.height,
                r.x0 + x2 * r.width,
                r.y0 + y2 * r.height,
            )
            mat = fitz.Matrix(3, 3)  # 3× zoom for readability
            pix = page.get_pixmap(matrix=mat, clip=clip)
            return pix.tobytes("png"), None
        except Exception as e:
            return None, f"PDF render error: {e}"
    else:
        try:
            from PIL import Image
        except ImportError:
            return None, "Pillow not installed — run: pip install pillow"
        try:
            img = Image.open(io.BytesIO(file_bytes))
            w, h = img.size
            crop = img.crop((
                int(x1 * w), int(y1 * h),
                int(x2 * w), int(y2 * h),
            ))
            buf = io.BytesIO()
            crop.save(buf, format="PNG")
            return buf.getvalue(), None
        except Exception as e:
            return None, f"Image crop error: {e}"


def build_correction_examples(corrections: list) -> str:
    """
    Format stored correction records into a few-shot example block to inject
    into the extraction prompt.

    corrections: list of dicts with keys field, equipment_name, extracted_value,
                 corrected_value, times_seen (as returned by get_ew_corrections).
    Returns an empty string if there are no corrections.
    """
    if not corrections:
        return ""

    lines = [
        "\nPAST CORRECTION EXAMPLES — learn from these patterns when reading similar values:\n"
    ]
    for c in corrections:
        field = c["field"]
        eq    = c.get("equipment_name") or ""
        label = f"{field} ({eq})" if eq else field
        times = c.get("times_seen", 1)
        lines.append(
            f"  • {label}: previously read as '{c['extracted_value']}' "
            f"but the correct value was '{c['corrected_value']}'"
            + (f"  [seen {times}×]" if times > 1 else "")
        )
    return "\n".join(lines)


def extract_plod(path: Path, api_key: str,
                 correction_examples: str = "") -> dict:
    """
    Send a PLOD file to Claude and return extracted structured data.
    Raises on API error. Returns dict with 'error' key on parse failure.

    correction_examples: optional string produced by build_correction_examples()
                         that is appended to the prompt before sending.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    prompt = _EXTRACTION_PROMPT
    if correction_examples:
        prompt = prompt + correction_examples

    content_blocks = _encode_file(path)
    content_blocks.append({"type": "text", "text": prompt})

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": content_blocks}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON parse failed: {e}",
            "raw_response": raw,
            "flags": [{"field": "root", "confidence": 0.0,
                        "issue": f"Could not parse Claude response as JSON: {e}"}],
        }


def batch_extract(paths: list[Path], api_key: str,
                  progress_callback=None,
                  correction_examples: str = "") -> tuple[list[dict], dict[str, bytes]]:
    """
    Extract multiple PLODs.

    progress_callback(i, total, filename) called per file.
    correction_examples: injected into every extraction call (from build_correction_examples).

    Returns:
        results:    list of extracted dicts, each with '_source_file' key.
        file_bytes: {filename: raw_bytes} for snippet rendering.
    """
    results    = []
    file_bytes = {}
    for i, path in enumerate(paths):
        if progress_callback:
            progress_callback(i, len(paths), path.name)
        file_bytes[path.name] = path.read_bytes()
        try:
            result = extract_plod(path, api_key, correction_examples=correction_examples)
        except Exception as e:
            result = {
                "error": str(e),
                "flags": [{"field": "root", "confidence": 0.0,
                            "issue": f"API call failed: {e}"}],
            }
        result["_source_file"] = path.name
        results.append(result)
    return results, file_bytes
