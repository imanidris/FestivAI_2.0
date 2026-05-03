"""
FestivAI Main Pipeline
Orchestrates the complete 5-step poster generation process.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config
from .step1_personalization import run_step1
from .step2_validation import run_step2
from .step3_content_generation import run_step3
from .step4_poster_assembly import run_step4
from .step5_rendering import run_step5


def run_pipeline(
    data_dir: Path | None = None,
    output_dir: Path | None = None,
    skip_validation: bool = False,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "llama3.1:8b",
    max_words: int = 12,
    variants: int = 3
) -> None:
    """
    Execute the complete FestivAI pipeline.

    Steps:
    1. Personalization: Load data and match users to artists/festivals
    2. Validation: Check that all assets and templates are valid
    3. Content Generation: Generate personalized copy with LLM
    4. Poster Assembly: Assemble SVG templates with content
    5. Rendering: Export final PNG posters and manifest
    """

    # Setup paths
    project_root = config.ROOT
    data_dir = data_dir or config.DATA
    output_dir = output_dir or config.POSTERS
    manifest_path = config.MANIFEST_CSV
    copy_cache_path = config.COPY_CACHE

    print("🎵 FestivAI Pipeline Starting...")
    print(f"   📂 Data directory: {data_dir}")
    print(f"   📁 Output directory: {output_dir}")
    print("")

    try:
        # Step 1: Personalization
        matches, personalization_summary = run_step1(data_dir)

        if not matches:
            print("❌ No personalized matches found. Check your data and try again.")
            return

        print("")

        # Step 2: Validation
        if not skip_validation:
            validation_results = run_step2(matches, project_root)

            if not validation_results.get("ready_for_generation", False):
                print("❌ Validation failed. Fix missing assets before continuing.")
                print("   Use --skip-validation to bypass validation checks.")
                return
        else:
            print("⚠️  Step 2: Validation skipped (--skip-validation flag)")

        print("")

        # Step 3: Content Generation
        copy_dict = run_step3(
            matches,
            copy_cache_path,
            max_words,
            variants,
            ollama_host,
            ollama_model
        )

        if not copy_dict:
            print("❌ No copy generated. Check LLM connection and try again.")
            return

        print("")

        # Step 4: Poster Assembly
        assembled_posters = run_step4(matches, copy_dict, project_root)

        if not assembled_posters:
            print("❌ No posters assembled. Check templates and assets.")
            return

        print("")

        # Step 5: Rendering & Export
        render_results = run_step5(
            matches,
            copy_dict,
            assembled_posters,
            output_dir,
            project_root,
            manifest_path
        )

        if render_results["status"] == "completed":
            print("")
            print("🎉 FestivAI pipeline completed successfully!")
            print(f"   🎨 Generated {render_results['total_rendered']} personalized posters")
            print(f"   📁 Output: {render_results['output_directory']}")
            print(f"   📋 Manifest: {render_results['manifest_path']}")
        else:
            print("❌ Pipeline failed during rendering step.")

    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FestivAI: Generate personalized festival poster ads using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                           # Run with defaults
  python -m src.main --skip-validation         # Skip asset validation
  python -m src.main --max-words 8             # Shorter copy text
  python -m src.main --ollama-host localhost   # Custom LLM host
        """
    )

    # Path options
    parser.add_argument("--data-dir", type=Path, help="Override data directory path")
    parser.add_argument("--output-dir", type=Path, help="Override output directory path")

    # Validation options
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip asset and template validation")

    # LLM options
    parser.add_argument("--ollama-host", default="http://localhost:11434",
                       help="Ollama server host (default: http://localhost:11434)")
    parser.add_argument("--ollama-model", default="llama3.1:8b",
                       help="Ollama model name (default: llama3.1:8b)")
    parser.add_argument("--max-words", type=int, default=12,
                       help="Maximum words in generated copy (default: 12)")
    parser.add_argument("--variants", type=int, default=3,
                       help="Number of copy variants to generate (default: 3)")

    # Debug options
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")

    args = parser.parse_args()

    # Run the pipeline
    run_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        skip_validation=args.skip_validation,
        ollama_host=args.ollama_host,
        ollama_model=args.ollama_model,
        max_words=args.max_words,
        variants=args.variants
    )


if __name__ == "__main__":
    main()