"""
Step 2: Validation
Validate that all required assets exist and templates can be parsed correctly.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree

from .config import IMAGE_MARKER_COLOR, TEXT_ZONES
from .step1_personalization import Match

SVG_NS = "http://www.w3.org/2000/svg"


def _normalize_color(value: str | None) -> str | None:
    """Normalize a fill value for comparison."""
    if value is None:
        return None
    return value.strip().lower()


def _extract_css_fills(root) -> dict[str, str]:
    """Extract CSS fill rules from <style> elements in the SVG."""
    css_fills = {}
    for style_elem in root.xpath(".//svg:style", namespaces={"svg": SVG_NS}):
        if style_elem.text:
            import re
            css_rules = re.findall(r'\.([^{]+)\s*\{\s*[^}]*fill:\s*([^;}\s]+)', style_elem.text)
            for class_name, fill_color in css_rules:
                css_fills[class_name.strip()] = _normalize_color(fill_color)
    return css_fills


def _get_element_fill_color(elem, css_fills: dict[str, str]) -> str | None:
    """Get the effective fill color of an element."""
    # Check direct fill attribute first
    direct_fill = _normalize_color(elem.get("fill"))
    if direct_fill:
        return direct_fill
    # Check CSS class
    class_attr = elem.get("class")
    if class_attr and class_attr in css_fills:
        return css_fills[class_attr]
    return None


def validate_template_zones(template_path: Path) -> dict[str, bool]:
    """
    Validate that a template SVG has all required zones.
    Returns dict with zone_name -> found status.
    """
    if not template_path.exists():
        return {"template_exists": False}

    try:
        tree = etree.parse(str(template_path))
        root = tree.getroot()
        css_fills = _extract_css_fills(root)

        zones_found = {
            "template_exists": True,
            "artist_image": False,
            "artist_name": False,
            "date": False,
            "copy_block": False
        }

        marker_color = _normalize_color(IMAGE_MARKER_COLOR)

        for elem in root.iter():
            tag = etree.QName(elem.tag).localname

            # Check for image marker rectangle
            if tag == "rect":
                fill = _get_element_fill_color(elem, css_fills)
                if fill == marker_color:
                    zones_found["artist_image"] = True

            # Check for text placeholder zones
            elif tag == "text":
                text_content = "".join(elem.itertext()).strip()
                for placeholder, zone_name in TEXT_ZONES.items():
                    if placeholder in text_content:
                        zones_found[zone_name] = True

        return zones_found

    except Exception as e:
        print(f"   ❌ Error parsing template {template_path}: {e}")
        return {"template_exists": True, "parse_error": str(e)}


def validate_artist_images(matches: list[Match], project_root: Path) -> dict[str, list[str]]:
    """
    Validate that all artist image files exist.
    Returns dict with 'missing' and 'found' file lists.
    """
    missing_images = []
    found_images = []

    unique_image_paths = set()
    for match in matches:
        unique_image_paths.add(match.artist.image_path)

    for image_path in unique_image_paths:
        full_path = project_root / image_path
        if full_path.exists():
            found_images.append(image_path)
        else:
            missing_images.append(image_path)

    return {"missing": missing_images, "found": found_images}


def validate_festival_fonts(matches: list[Match], project_root: Path) -> dict[str, list[str]]:
    """
    Validate that all festival font files exist.
    Returns dict with 'missing' and 'found' font lists.
    """
    missing_fonts = []
    found_fonts = []

    unique_font_paths = set()
    for match in matches:
        for font_path in match.festival.font_paths:
            unique_font_paths.add(font_path)

    for font_path in unique_font_paths:
        full_path = project_root / font_path
        if full_path.exists():
            found_fonts.append(font_path)
        else:
            missing_fonts.append(font_path)

    return {"missing": missing_fonts, "found": found_fonts}


def validate_templates(matches: list[Match], project_root: Path) -> dict[str, dict]:
    """
    Validate all unique templates used in matches.
    Returns dict with template_path -> validation results.
    """
    template_results = {}

    unique_templates = set()
    for match in matches:
        unique_templates.add(match.festival.template_path)

    for template_path in unique_templates:
        full_path = project_root / template_path
        template_results[template_path] = validate_template_zones(full_path)

    return template_results


def run_step2(matches: list[Match], project_root: Path) -> dict:
    """
    Execute Step 2: Validate all assets and templates.
    Returns validation results summary.
    """
    print("🔍 Step 2: Validating assets and templates...")

    if not matches:
        print("   ⚠️  No matches to validate")
        return {"status": "no_matches"}

    # Validate artist images
    print("   📸 Checking artist images...")
    image_validation = validate_artist_images(matches, project_root)
    if image_validation["missing"]:
        print(f"   ❌ Missing {len(image_validation['missing'])} artist images:")
        for img in image_validation["missing"][:3]:  # Show first 3
            print(f"      - {img}")
        if len(image_validation["missing"]) > 3:
            print(f"      ... and {len(image_validation['missing']) - 3} more")
    else:
        print(f"   ✅ All {len(image_validation['found'])} artist images found")

    # Validate festival fonts
    print("   🔤 Checking festival fonts...")
    font_validation = validate_festival_fonts(matches, project_root)
    if font_validation["missing"]:
        print(f"   ❌ Missing {len(font_validation['missing'])} font files:")
        for font in font_validation["missing"]:
            print(f"      - {font}")
    else:
        print(f"   ✅ All {len(font_validation['found'])} font files found")

    # Validate templates
    print("   🎨 Checking SVG templates...")
    template_validation = validate_templates(matches, project_root)

    templates_valid = True
    for template_path, results in template_validation.items():
        if not results.get("template_exists", False):
            print(f"   ❌ Template not found: {template_path}")
            templates_valid = False
            continue

        if "parse_error" in results:
            print(f"   ❌ Template parse error: {template_path}")
            templates_valid = False
            continue

        # Check required zones
        required_zones = ["artist_image", "artist_name", "date", "copy_block"]
        missing_zones = [zone for zone in required_zones if not results.get(zone, False)]

        if missing_zones:
            print(f"   ❌ Template {template_path} missing zones: {missing_zones}")
            templates_valid = False
        else:
            print(f"   ✅ Template {template_path} - all zones found")

    # Overall validation summary
    all_valid = (
        len(image_validation["missing"]) == 0 and
        len(font_validation["missing"]) == 0 and
        templates_valid
    )

    validation_summary = {
        "status": "valid" if all_valid else "invalid",
        "images": image_validation,
        "fonts": font_validation,
        "templates": template_validation,
        "ready_for_generation": all_valid
    }

    if all_valid:
        print("   ✅ All validation checks passed - ready for poster generation!")
    else:
        print("   ❌ Validation failed - fix missing assets before continuing")

    return validation_summary