"""
Step 3: Content Generation
Generate personalized copy text for each poster using LLM with caching.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from .step1_personalization import Match


def load_copy_cache(cache_path: Path) -> dict[str, str]:
    """Load cached copy from disk."""
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return {}


def save_copy_cache(cache: dict[str, str], cache_path: Path) -> None:
    """Save copy cache to disk."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def call_ollama(
    prompt: str,
    system_prompt: str,
    host: str = "http://localhost:11434",
    model: str = "llama3.1:8b"
) -> str:
    """Call Ollama LLM and return generated text."""
    response = requests.post(
        f"{host}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def score_copy_variant(text: str, max_words: int) -> int:
    """Score copy variants for quality. Lower score is better."""
    word_count = len(text.split())
    score = 0

    # Penalize length violations
    if word_count > max_words:
        score += (word_count - max_words) * 10

    # Penalize style violations
    if "!" in text:
        score += 5
    if not text.isupper():
        score += 3

    # Penalize banned clichés
    banned_words = ["AMAZING", "INCREDIBLE", "UNFORGETTABLE", "EPIC"]
    for banned in banned_words:
        if banned in text.upper():
            score += 5

    return score


def generate_copy_for_match(
    match: Match,
    cache_path: Path,
    max_words: int = 12,
    n_variants: int = 3,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "llama3.1:8b",
) -> str:
    """Generate personalized copy for a specific match."""

    cache_key = f"{match.user.user_id}:{match.artist.artist_id}:{match.festival.festival_id}"

    # Check cache first
    cache = load_copy_cache(cache_path)
    if cache_key in cache:
        return cache[cache_key]

    # Create prompts
    system_prompt = f"""You write short promotional taglines for music festival ads.

Rules:
- ONE sentence only, maximum {max_words} words.
- ALL CAPS output.
- No exclamation marks.
- No clichés like "amazing", "incredible", "unforgettable", "epic".
- Match the energy of the genre — punchy and direct, never corporate.
- Output the tagline only, no preamble, no quotes."""

    user_prompt = (
        f"Generate a tagline for an ad promoting {match.artist.name} at {match.festival.name}. "
        f"Genre: {match.artist.genre}. "
        f"Performance date: {match.artist.performance_date}. "
        f"Target user: {match.user.name}."
    )

    # Generate variants
    variants = []
    for _ in range(n_variants):
        try:
            variant = call_ollama(user_prompt, system_prompt, ollama_host, ollama_model)
            variants.append(variant)
        except requests.RequestException as e:
            print(f"   ⚠️  LLM call failed for {match.poster_id}: {e}")
            continue

    # Pick best variant or use fallback
    if variants:
        best_copy = min(variants, key=lambda x: score_copy_variant(x, max_words)).upper()
    else:
        # Fallback copy when LLM is unavailable
        best_copy = f"{match.artist.name.upper()} LIVE AT {match.festival.name.upper()}"

    # Cache the result
    cache[cache_key] = best_copy
    save_copy_cache(cache, cache_path)

    return best_copy


def run_step3(
    matches: list[Match],
    cache_path: Path,
    max_words: int = 12,
    n_variants: int = 3,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "llama3.1:8b",
) -> dict[str, str]:
    """
    Execute Step 3: Generate personalized copy for all matches.
    Returns dict mapping poster_id -> generated_copy.
    """
    print("✨ Step 3: Generating personalized copy with LLM...")

    if not matches:
        print("   ⚠️  No matches to generate copy for")
        return {}

    # Test LLM connection
    try:
        test_response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if test_response.status_code == 200:
            print(f"   🤖 Connected to Ollama at {ollama_host}")
        else:
            print(f"   ⚠️  Ollama server responded with status {test_response.status_code}")
    except requests.RequestException:
        print(f"   ⚠️  Cannot connect to Ollama at {ollama_host} - will use fallback copy")

    # Generate copy for each match
    copy_results = {}
    cache_hits = 0

    print(f"   📝 Generating copy for {len(matches)} poster combinations...")

    for i, match in enumerate(matches, 1):
        # Show progress periodically
        if i % 10 == 0 or i == len(matches):
            print(f"   📝 Progress: {i}/{len(matches)} posters")

        # Check if already cached
        cache = load_copy_cache(cache_path)
        cache_key = f"{match.user.user_id}:{match.artist.artist_id}:{match.festival.festival_id}"

        if cache_key in cache:
            copy_results[match.poster_id] = cache[cache_key]
            cache_hits += 1
        else:
            copy_text = generate_copy_for_match(
                match, cache_path, max_words, n_variants, ollama_host, ollama_model
            )
            copy_results[match.poster_id] = copy_text

    # Summary
    new_generations = len(matches) - cache_hits
    print(f"   ✅ Copy generation complete:")
    print(f"      📋 {cache_hits} from cache, {new_generations} newly generated")
    print(f"      💾 Cache saved to: {cache_path}")

    # Show sample results
    if copy_results:
        print(f"   🎯 Sample generated copy:")
        for poster_id, copy_text in list(copy_results.items())[:3]:
            # Find the match for context
            match = next(m for m in matches if m.poster_id == poster_id)
            print(f"      {match.user.name} + {match.artist.name}: \"{copy_text}\"")

    return copy_results