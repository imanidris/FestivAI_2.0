"""
Step 4: Poster Assembly
Load SVG templates and assemble them with personalized content (artist image, text, copy).
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree

from .config import IMAGE_MARKER_COLOR, TEXT_ZONES
from .step1_personalization import Match

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def _normalize_color(value: str | None) -> str | None:
    """Normalize a fill value for comparison."""
    if value is None:
        return None
    return value.strip().lower()


def _extract_css_fills(root) -> dict[str, str]:
    """Extract CSS fill rules from <style> elements."""
    css_fills = {}
    for style_elem in root.xpath(".//svg:style", namespaces={"svg": SVG_NS}):
        if style_elem.text:
            import re
            css_rules = re.findall(r'\.([^{]+)\s*\{\s*[^}]*fill:\s*([^;}\s]+)', style_elem.text)
            for class_name, fill_color in css_rules:
                css_fills[class_name.strip()] = _normalize_color(fill_color)
    return css_fills


def _get_element_fill_color(elem, css_fills: dict[str, str]) -> str | None:
    """Get effective fill color considering both direct and CSS class fills."""
    # Check direct fill attribute
    direct_fill = _normalize_color(elem.get("fill"))
    if direct_fill:
        return direct_fill
    # Check CSS class
    class_attr = elem.get("class")
    if class_attr and class_attr in css_fills:
        return css_fills[class_attr]
    return None


def _get_float_attr(elem, attr: str, default: float = 0.0) -> float:
    """Read a float attribute from element."""
    val = elem.get(attr)
    return float(val) if val is not None else default


def parse_template_zones(template_path: Path) -> tuple[etree._ElementTree, dict]:
    """
    Parse SVG template and identify zones for content replacement.
    Returns (tree, zones_dict) where zones_dict maps zone_name -> element.
    """
    tree = etree.parse(str(template_path))
    root = tree.getroot()
    css_fills = _extract_css_fills(root)

    zones = {}
    marker_color = _normalize_color(IMAGE_MARKER_COLOR)

    for elem in root.iter():
        tag = etree.QName(elem.tag).localname

        # Find image zone (gray rectangle)
        if tag == "rect":
            fill = _get_element_fill_color(elem, css_fills)
            if fill == marker_color:
                zones["artist_image"] = {
                    "element": elem,
                    "x": _get_float_attr(elem, "x"),
                    "y": _get_float_attr(elem, "y"),
                    "width": _get_float_attr(elem, "width"),
                    "height": _get_float_attr(elem, "height"),
                }

        # Find text zones (placeholder strings)
        elif tag == "text":
            text_content = "".join(elem.itertext()).strip()
            for placeholder, zone_name in TEXT_ZONES.items():
                if placeholder in text_content:
                    zones[zone_name] = {
                        "element": elem,
                        "placeholder": placeholder,
                        "original_text": text_content
                    }
                    break

    return tree, zones


def replace_text_content(zone_info: dict, new_text: str) -> None:
    """Replace text content in a text zone while preserving styling."""
    elem = zone_info["element"]

    # Clear all child elements (tspan, etc.)
    for child in list(elem):
        elem.remove(child)

    # Handle text wrapping for long text
    if zone_info.get("placeholder") in ["{{ARTIST_NAME}}", "{{COPY}}"]:
        _create_wrapped_text(elem, new_text, zone_info.get("placeholder"))
    else:
        # For short text like DATE, just set directly
        elem.text = new_text


def _create_wrapped_text(elem, text: str, placeholder: str) -> None:
    """Create multi-line text using tspan elements for text wrapping."""
    # Define text zone parameters with pixel boundaries
    if placeholder == "{{ARTIST_NAME}}":
        text_anchor_x = 584
        zone_left = 242
        zone_right = 924
        max_width = zone_right - zone_left  # 682 pixels
        line_height = "1.2em"
        font_size = 79.65  # from cls-8 in SVG
        avg_char_width = font_size * 0.6  # Rough estimate for character width
    elif placeholder == "{{COPY}}":
        text_anchor_x = 775
        zone_left = 564
        zone_right = 1020
        max_width = zone_right - zone_left  # 456 pixels
        line_height = "1.1em"
        font_size = 36  # from cls-6 in SVG
        avg_char_width = font_size * 0.6  # Rough estimate for character width
    else:
        elem.text = text
        return

    # Calculate approximate characters per line based on pixel width
    max_chars_per_line = int(max_width / avg_char_width)

    # Split text into lines
    lines = _wrap_text_to_lines(text, max_chars_per_line)

    if len(lines) == 1:
        # Single line - just set text directly
        elem.text = lines[0]
        return

    # Multi-line - create tspan elements
    elem.text = ""  # Clear text content

    for i, line in enumerate(lines):
        tspan = etree.SubElement(elem, "tspan")
        tspan.text = line
        tspan.set("x", "0")

        if i == 0:
            tspan.set("y", "0")
        else:
            tspan.set("dy", line_height)


def _wrap_text_to_lines(text: str, max_chars: int) -> list[str]:
    """Wrap text into multiple lines, trying to break at word boundaries."""
    if len(text) <= max_chars:
        return [text]

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Check if adding this word would exceed the limit
        test_line = f"{current_line} {word}".strip()

        if len(test_line) <= max_chars:
            current_line = test_line
        else:
            # Start new line
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Single word is too long - force break
                lines.append(word[:max_chars-3] + "...")
                current_line = ""

    # Add the last line
    if current_line:
        lines.append(current_line)

    return lines


def replace_image_zone(zone_info: dict, image_path: str) -> None:
    """Replace marker rectangle with an SVG image element."""
    rect = zone_info["element"]
    parent = rect.getparent()

    if parent is None:
        raise RuntimeError("Image zone rect has no parent")

    # Create new image element
    image = etree.SubElement(parent, f"{{{SVG_NS}}}image")
    image.set("x", str(zone_info["x"]))
    image.set("y", str(zone_info["y"]))
    image.set("width", str(zone_info["width"]))
    image.set("height", str(zone_info["height"]))
    image.set("preserveAspectRatio", "xMidYMid slice")  # CSS object-fit: cover equivalent

    # Set both href attributes for compatibility
    image.set("href", image_path)
    image.set(f"{{{XLINK_NS}}}href", image_path)

    # Remove the marker rectangle
    parent.remove(rect)


def assemble_poster(
    match: Match,
    copy_text: str,
    project_root: Path
) -> etree._ElementTree:
    """
    Assemble a complete poster by loading template and replacing all zones.
    Returns the modified SVG tree ready for rendering.
    """
    template_path = project_root / match.festival.template_path

    # Parse template and find zones
    tree, zones = parse_template_zones(template_path)

    # Validate all required zones are present
    required_zones = ["artist_image", "artist_name", "date", "copy_block"]
    missing_zones = [zone for zone in required_zones if zone not in zones]
    if missing_zones:
        raise RuntimeError(f"Template missing required zones: {missing_zones}")

    # Replace content in each zone
    try:
        # Replace artist image
        replace_image_zone(zones["artist_image"], match.artist.image_path)

        # Replace text content
        replace_text_content(zones["artist_name"], match.artist.name.upper())
        replace_text_content(zones["date"], match.artist.performance_date)
        replace_text_content(zones["copy_block"], copy_text)

    except Exception as e:
        raise RuntimeError(f"Error assembling poster for {match.poster_id}: {e}")

    return tree


def serialize_svg(tree: etree._ElementTree) -> bytes:
    """Convert SVG tree to bytes for rendering."""
    return etree.tostring(tree, xml_declaration=True, encoding="utf-8")


def run_step4(
    matches: list[Match],
    copy_dict: dict[str, str],
    project_root: Path
) -> dict[str, bytes]:
    """
    Execute Step 4: Assemble SVG posters for all matches.
    Returns dict mapping poster_id -> svg_bytes.
    """
    print("🎨 Step 4: Assembling personalized posters...")

    if not matches:
        print("   ⚠️  No matches to assemble")
        return {}

    if not copy_dict:
        print("   ⚠️  No copy text provided")
        return {}

    assembled_posters = {}
    failed_assemblies = []

    print(f"   🔧 Assembling {len(matches)} poster combinations...")

    for i, match in enumerate(matches, 1):
        # Show progress
        if i % 10 == 0 or i == len(matches):
            print(f"   🔧 Progress: {i}/{len(matches)} posters assembled")

        try:
            # Get copy text for this poster
            copy_text = copy_dict.get(match.poster_id, "")
            if not copy_text:
                print(f"   ⚠️  No copy text for {match.poster_id}, using fallback")
                copy_text = f"{match.artist.name.upper()} LIVE"

            # Assemble the poster
            svg_tree = assemble_poster(match, copy_text, project_root)
            svg_bytes = serialize_svg(svg_tree)

            assembled_posters[match.poster_id] = svg_bytes

        except Exception as e:
            print(f"   ❌ Failed to assemble {match.poster_id}: {e}")
            failed_assemblies.append(match.poster_id)

    # Summary
    success_count = len(assembled_posters)
    print(f"   ✅ Assembly complete:")
    print(f"      🎨 {success_count} posters assembled successfully")
    if failed_assemblies:
        print(f"      ❌ {len(failed_assemblies)} failed assemblies")
        for failed_id in failed_assemblies[:3]:
            print(f"         - {failed_id}")

    return assembled_posters