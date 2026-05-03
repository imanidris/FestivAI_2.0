"""
Step 1: Data Loading & Personalization
Load CSV data and match users to their favorite artists at festivals they can attend.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Festival:
    festival_id: str
    name: str
    date_range: str
    location: str
    template_path: str
    font_paths: list[str]


@dataclass
class Artist:
    artist_id: str
    name: str
    genre: str
    image_path: str
    festival_id: str
    performance_date: str


@dataclass
class User:
    user_id: str
    name: str
    favorite_artist_ids: list[str]
    preferred_location: list[str]


@dataclass
class Match:
    """A personalized match: user + artist + festival + performance date"""
    user: User
    festival: Festival
    artist: Artist

    @property
    def poster_id(self) -> str:
        """Unique identifier for this poster combination"""
        return f"{self.user.user_id}_{self.artist.artist_id}_{self.festival.festival_id}"


def load_festivals(csv_path: Path) -> dict[str, Festival]:
    """Load festivals from CSV file."""
    festivals = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            festivals[row["festival_id"]] = Festival(
                festival_id=row["festival_id"],
                name=row["name"],
                date_range=row["date_range"],
                location=row["location"],
                template_path=row["template_path"],
                font_paths=[fp.strip() for fp in row["font_paths"].split(",") if fp.strip()],
            )
    return festivals


def load_artists(csv_path: Path) -> list[Artist]:
    """Load artists from CSV file. Returns list since artists can have multiple festival performances."""
    artists = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            artists.append(Artist(
                artist_id=row["artist_id"],
                name=row["name"],
                genre=row["genre"],
                image_path=row["image_path"],
                festival_id=row["festival_id"],
                performance_date=row["performance_date"],
            ))
    return artists


def load_users(csv_path: Path) -> list[User]:
    """Load users from CSV file."""
    users = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            users.append(User(
                user_id=row["user_id"],
                name=row["name"],
                favorite_artist_ids=[aid.strip() for aid in row["favorite_artist_ids"].split(",") if aid.strip()],
                preferred_location=[loc.strip() for loc in row["preferred_location"].split(",") if loc.strip()],
            ))
    return users


def find_personalized_matches(
    users: list[User],
    festivals: dict[str, Festival],
    artists: list[Artist],
) -> list[Match]:
    """
    Find all valid (user, artist, festival) combinations for poster generation.

    Logic:
    1. For each user
    2. For each of their favorite artists (in preference order)
    3. Find all festivals where that artist is performing
    4. Filter to festivals in user's preferred locations
    5. Create a match for each valid combination
    """
    matches = []

    for user in users:
        user_matches = 0

        # Walk through user's favorite artists in preference order
        for artist_id in user.favorite_artist_ids:
            # Find all performances by this artist
            artist_performances = [a for a in artists if a.artist_id == artist_id]

            for artist_performance in artist_performances:
                # Get the festival for this performance
                festival = festivals.get(artist_performance.festival_id)
                if not festival:
                    continue

                # Check if user would attend this festival (location filter)
                if festival.location in user.preferred_location:
                    matches.append(Match(
                        user=user,
                        festival=festival,
                        artist=artist_performance
                    ))
                    user_matches += 1

        if user_matches == 0:
            print(f"[warn] User {user.user_id} ({user.name}) has no favorite artists at accessible festivals")

    return matches


def get_personalization_summary(matches: list[Match]) -> dict:
    """Get summary statistics about the personalization results."""
    if not matches:
        return {"total_users": 0, "total_matches": 0, "avg_posters_per_user": 0}

    users_with_matches = len(set(match.user.user_id for match in matches))
    total_matches = len(matches)
    avg_posters = round(total_matches / users_with_matches, 1) if users_with_matches > 0 else 0

    # Count matches per user
    user_counts = {}
    for match in matches:
        user_id = match.user.user_id
        user_counts[user_id] = user_counts.get(user_id, 0) + 1

    return {
        "total_users_with_matches": users_with_matches,
        "total_poster_combinations": total_matches,
        "avg_posters_per_user": avg_posters,
        "user_breakdown": user_counts
    }


def run_step1(data_dir: Path) -> tuple[list[Match], dict]:
    """
    Execute Step 1: Load data and find personalized matches.
    Returns (matches, summary) for use in subsequent steps.
    """
    print("📊 Step 1: Loading data and finding personalized matches...")

    # Load all data
    festivals = load_festivals(data_dir / "festivals.csv")
    artists = load_artists(data_dir / "artists.csv")
    users = load_users(data_dir / "users.csv")

    print(f"   ✅ Loaded: {len(festivals)} festivals, {len(artists)} artist performances, {len(users)} users")

    # Find personalized matches
    matches = find_personalized_matches(users, festivals, artists)
    summary = get_personalization_summary(matches)

    if matches:
        print(f"   🎯 Found {summary['total_poster_combinations']} personalized poster combinations")
        print(f"   👥 {summary['total_users_with_matches']} users will get {summary['avg_posters_per_user']} posters on average")
    else:
        print("   ❌ No valid matches found!")

    return matches, summary