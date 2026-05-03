"""
Step 5: Rendering & Export
Convert assembled SVG posters to final PNG files and generate manifest.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .step1_personalization import Match


def rasterize_svg_to_png(svg_bytes: bytes) -> bytes:
    """
    Convert SVG bytes to PNG bytes using available rasterizer.
    Tries resvg-py first (better quality), falls back to cairosvg.
    """
    try:
        # Try resvg-py (preferred - higher quality text rendering)
        import resvg_py  # type: ignore[import-not-found]
        return resvg_py.svg_to_bytes(svg_string=svg_bytes.decode("utf-8"))

    except ImportError:
        try:
            # Fall back to cairosvg
            import cairosvg  # type: ignore[import-not-found]
            return cairosvg.svg2png(bytestring=svg_bytes)

        except ImportError:
            raise RuntimeError(
                "No SVG rasterizer available. Install either 'resvg-py' or 'cairosvg':\n"
                "  pip install resvg-py  # (recommended)\n"
                "  pip install cairosvg  # (fallback)"
            )


def save_poster_png(
    poster_id: str,
    svg_bytes: bytes,
    output_dir: Path
) -> Path:
    """
    Render SVG to PNG and save to disk.
    Returns the path to the saved PNG file.
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    output_path = output_dir / f"{poster_id}.png"

    try:
        # Render SVG to PNG
        png_bytes = rasterize_svg_to_png(svg_bytes)

        # Save to disk
        output_path.write_bytes(png_bytes)

        return output_path

    except Exception as e:
        raise RuntimeError(f"Failed to render {poster_id}: {e}")


def generate_manifest(
    matches: list[Match],
    copy_dict: dict[str, str],
    rendered_paths: dict[str, Path],
    project_root: Path,
    manifest_path: Path
) -> None:
    """
    Generate comprehensive manifest CSV tracking all generated posters.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_data = []

    for match in matches:
        poster_id = match.poster_id
        copy_text = copy_dict.get(poster_id, "")
        output_path = rendered_paths.get(poster_id)

        if output_path:
            relative_path = output_path.relative_to(project_root)
            status = "success"
        else:
            relative_path = "FAILED"
            status = "failed"

        manifest_data.append({
            "poster_id": poster_id,
            "user_id": match.user.user_id,
            "user_name": match.user.name,
            "artist_id": match.artist.artist_id,
            "artist_name": match.artist.name,
            "festival_id": match.festival.festival_id,
            "festival_name": match.festival.name,
            "performance_date": match.artist.performance_date,
            "copy_text": copy_text,
            "output_path": str(relative_path),
            "status": status
        })

    # Write CSV manifest
    if manifest_data:
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(manifest_data[0].keys()))
            writer.writeheader()
            writer.writerows(manifest_data)


def run_step5(
    matches: list[Match],
    copy_dict: dict[str, str],
    assembled_posters: dict[str, bytes],
    output_dir: Path,
    project_root: Path,
    manifest_path: Path
) -> dict:
    """
    Execute Step 5: Render SVG posters to PNG and generate manifest.
    Returns summary of rendering results.
    """
    print("🖼️  Step 5: Rendering posters to PNG and generating manifest...")

    if not matches:
        print("   ⚠️  No matches to render")
        return {"status": "no_matches"}

    if not assembled_posters:
        print("   ⚠️  No assembled posters to render")
        return {"status": "no_posters"}

    # Test rasterizer availability
    try:
        test_svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'
        rasterize_svg_to_png(test_svg)
        print("   🎨 SVG rasterizer ready")
    except RuntimeError as e:
        print(f"   ❌ Rasterizer error: {e}")
        return {"status": "rasterizer_error", "error": str(e)}

    # Render all posters
    rendered_paths = {}
    failed_renders = []

    print(f"   🖼️  Rendering {len(assembled_posters)} posters to PNG...")

    for i, (poster_id, svg_bytes) in enumerate(assembled_posters.items(), 1):
        # Show progress
        if i % 10 == 0 or i == len(assembled_posters):
            print(f"   🖼️  Progress: {i}/{len(assembled_posters)} posters rendered")

        try:
            output_path = save_poster_png(poster_id, svg_bytes, output_dir)
            rendered_paths[poster_id] = output_path

        except RuntimeError as e:
            print(f"   ❌ Render failed for {poster_id}: {e}")
            failed_renders.append(poster_id)

    # Generate manifest
    print("   📋 Generating manifest...")
    generate_manifest(matches, copy_dict, rendered_paths, project_root, manifest_path)

    # Calculate summary statistics
    success_count = len(rendered_paths)
    total_attempts = len(assembled_posters)
    user_counts = {}

    for match in matches:
        if match.poster_id in rendered_paths:
            user_name = match.user.name
            user_counts[user_name] = user_counts.get(user_name, 0) + 1

    # Print results summary
    print(f"   ✅ Rendering complete:")
    print(f"      🎨 {success_count}/{total_attempts} posters rendered successfully")
    print(f"      📁 Output directory: {output_dir}")
    print(f"      📋 Manifest: {manifest_path}")

    if failed_renders:
        print(f"      ❌ {len(failed_renders)} render failures")

    # Show user breakdown
    if user_counts:
        print(f"   👥 Posters per user:")
        for user_name, count in list(user_counts.items())[:8]:
            print(f"      {user_name}: {count} posters")
        if len(user_counts) > 8:
            print(f"      ... and {len(user_counts) - 8} more users")

    return {
        "status": "completed",
        "total_rendered": success_count,
        "total_failed": len(failed_renders),
        "output_directory": str(output_dir),
        "manifest_path": str(manifest_path),
        "user_breakdown": user_counts
    }