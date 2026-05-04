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
    # Combine system and user prompt for /api/generate endpoint
    full_prompt = f"{system_prompt}\n\n{prompt}"

    response = requests.post(
        f"{host}/api/generate",
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    raw_response = response.json()["response"].strip()

    # Clean up AI output artifacts (inspired by legacy approach)
    cleaned = raw_response.strip('"').strip("'").split("\n")[0].strip()

    # Remove common AI prefixes/suffixes
    prefixes_to_remove = ["Here's a slogan:", "Slogan:", "Here it is:", "The slogan is:"]
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()

    # Remove unwanted punctuation and symbols
    import re
    # Remove all emoji and special symbols
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    cleaned = emoji_pattern.sub('', cleaned)

    # Remove punctuation
    cleaned = cleaned.replace("!", "").replace("@", "").replace("#", "").replace("*", "")
    cleaned = cleaned.replace("'", "").replace('"', '').replace("(", "").replace(")", "")
    cleaned = cleaned.replace(":", " ").replace("-", " ").replace(".", " ")

    # Clean up extra spaces
    cleaned = " ".join(cleaned.split())

    return cleaned


def score_copy_variant(text: str, max_words: int, artist_name: str = "", min_words: int = 6) -> int:
    """Score copy variants for quality. Lower score is better."""
    word_count = len(text.split())
    score = 0

    # Penalize length violations
    if word_count > max_words:
        score += (word_count - max_words) * 10
    if word_count < min_words:
        score += (min_words - word_count) * 15  # Heavy penalty for too short

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

    # Reward artist name inclusion (new from legacy approach)
    if artist_name and artist_name.upper() not in text.upper():
        score += 15  # Heavy penalty for missing artist name

    # Reward action-oriented language (new enhancement)
    action_words = ["CATCH", "FEEL", "WITNESS", "EXPERIENCE", "SEE", "HEAR", "WATCH", "LIVE", "TAKES", "BRINGS", "DANCE", "MOVE"]
    has_action_word = any(action in text.upper() for action in action_words)
    if not has_action_word:
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

    # Create prompts with examples and clear requirements
    system_prompt = f"""You are a slogan generator for music festival posters.
Only return a slogan — nothing else. The slogan must:
- Be a bold, punchy phrase
- Be 6 to {max_words} words (minimum 6, maximum {max_words})
- Include the artist name: '{match.artist.name}'
- Use action-oriented, visual language
- Avoid punctuation, emojis, and full sentences
- No clichés like "amazing", "incredible", "unforgettable", "epic"

Examples of great festival slogans (6+ words):
- CATCH BLADEE LIVE AT PUKKELPOP FESTIVAL
- FEEL MARINA'S ENERGY THIS SUMMER NIGHT
- TYLER TAKES THE STAGE IN BELGIUM
- WITNESS CLAIRO'S MAGIC AT THE FESTIVAL
- EXPERIENCE MAU P'S BEATS ALL NIGHT
- DANCE TO THE RHYTHM OF TECHNO

Now, return the slogan for: {match.artist.name}
(Only reply with the slogan. No intro, no quotes.)"""

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
        best_copy = min(variants, key=lambda x: score_copy_variant(x, max_words, match.artist.name, 6)).upper()
    else:
        # Fallback copy when LLM is unavailable (includes artist name by design)
        best_copy = f"CATCH {match.artist.name.upper()} LIVE AT PUKKELPOP FESTIVAL"

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