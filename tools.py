"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _call_groq(prompt: str, temperature: float = 0.7) -> str:
    """Call Groq and return the model response text."""
    client = _get_groq_client()
    print("Calling Groq...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FitFindr, a concise and friendly secondhand fashion "
                    "stylist. Give practical, specific outfit advice."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=350,
    )
    return response.choices[0].message.content.strip()


def _tokenize(text: str) -> set[str]:
    """Convert text into searchable lowercase tokens."""
    if not text:
        return set()

    stopwords = {
        "a", "an", "and", "the", "for", "with", "under", "over", "in", "on",
        "to", "of", "i", "im", "i'm", "looking", "find", "want", "need",
        "size", "what", "out", "there", "how", "would", "style", "it",
    }
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {word for word in words if word not in stopwords and len(word) > 1}


def _listing_search_text(listing: dict) -> str:
    """Flatten listing fields into one searchable string."""
    parts = [
        str(listing.get("title", "")),
        str(listing.get("description", "")),
        str(listing.get("category", "")),
        str(listing.get("size", "")),
        str(listing.get("condition", "")),
        str(listing.get("brand", "")),
        str(listing.get("platform", "")),
        " ".join(map(str, listing.get("style_tags", []) or [])),
        " ".join(map(str, listing.get("colors", []) or [])),
    ]
    return " ".join(parts).lower()


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    """
    try:
        listings = load_listings()
    except Exception:
        return []

    query_tokens = _tokenize(description)
    if not query_tokens:
        return []

    matches: list[tuple[int, dict]] = []

    for listing in listings:
        price = listing.get("price")

        if max_price is not None:
            try:
                if float(price) > float(max_price):
                    continue
            except (TypeError, ValueError):
                continue

        if size:
            requested_size = str(size).lower().strip()
            listing_size = str(listing.get("size", "")).lower().strip()
            if requested_size not in listing_size:
                continue

        search_text = _listing_search_text(listing)
        listing_tokens = _tokenize(search_text)

        score = len(query_tokens & listing_tokens)

        # Give a small bonus when the exact phrase appears in the listing text.
        if description and description.lower().strip() in search_text:
            score += 3

        if score > 0:
            matches.append((score, listing))

    matches.sort(key=lambda pair: (pair[0], -float(pair[1].get("price", 0))), reverse=True)
    return [listing for score, listing in matches]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
    """
    if not new_item:
        return "I need a selected item before I can suggest an outfit."

    wardrobe_items = (wardrobe or {}).get("items", []) or []

    item_summary = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Category: {new_item.get('category', '')}\n"
        f"Style tags: {', '.join(map(str, new_item.get('style_tags', []) or []))}\n"
        f"Colors: {', '.join(map(str, new_item.get('colors', []) or []))}\n"
        f"Price: ${new_item.get('price', 'unknown')}\n"
        f"Platform: {new_item.get('platform', 'unknown')}"
    )

    if not wardrobe_items:
        prompt = f"""
The user is considering buying this secondhand item:

{item_summary}

Their wardrobe is empty or not provided. Suggest 1-2 complete outfit ideas using common wardrobe basics someone could own or buy later. Keep it specific, practical, and stylish.
"""
    else:
        formatted_wardrobe = "\n".join(
            f"- {item.get('name') or item.get('title') or item.get('category', 'item')}: "
            f"{item.get('description', '')} "
            f"{', '.join(map(str, item.get('colors', []) or []))} "
            f"{', '.join(map(str, item.get('style_tags', []) or []))}"
            for item in wardrobe_items
        )

        prompt = f"""
The user is considering buying this secondhand item:

{item_summary}

Here are items in the user's current wardrobe:
{formatted_wardrobe}

Suggest 1-2 complete outfit combinations using the new item and specific wardrobe pieces where possible. Include the overall vibe and one styling tip.
"""

    try:
        return _call_groq(prompt, temperature=0.7)
    except Exception as e:
        print(f"Error occurred while calling Groq: {e}")

        title = new_item.get("title", "this thrifted piece")
        colors = ", ".join(map(str, new_item.get("colors", []) or []))
        color_text = f" in {colors}" if colors else ""
        if wardrobe_items:
            first_piece = wardrobe_items[0].get("name") or wardrobe_items[0].get("title") or "a favorite wardrobe staple"
            return (
                f"Style {title}{color_text} with {first_piece} and simple shoes to keep the focus on the thrifted find. "
                "Add one clean accessory and keep the silhouette balanced."
            )
        return (
            f"Style {title}{color_text} with relaxed denim, simple sneakers or boots, and a neutral layer. "
            "Keep accessories minimal so the thrifted item feels intentional."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """
    if not outfit or not outfit.strip():
        return "Unable to create fit card because outfit information is missing."

    if not new_item:
        return "Unable to create fit card because item information is missing."

    title = new_item.get("title", "this thrifted find")
    price = new_item.get("price", "unknown")
    platform = new_item.get("platform", "a secondhand platform")

    prompt = f"""
Create a short shareable outfit caption for an Instagram/TikTok outfit post.

Item:
- Title: {title}
- Price: ${price}
- Platform: {platform}
- Description: {new_item.get('description', '')}
- Colors: {', '.join(map(str, new_item.get('colors', []) or []))}
- Style tags: {', '.join(map(str, new_item.get('style_tags', []) or []))}

Outfit suggestion:
{outfit}

Requirements:
- 2 to 4 sentences
- Casual and authentic, like a real OOTD caption
- Mention the item name, price, and platform naturally once
- Do not sound like a product description
"""

    try:
        return _call_groq(prompt, temperature=0.95)
    except Exception as e:
        print(f"Error occurred while calling Groq: {e}")
        return (
            f"Found {title} on {platform} for ${price} and it completely pulls the outfit together. "
            f"{outfit} Thrifted, styled, and definitely getting repeated."
        )
