"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.
    """
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query.

    This intentionally uses lightweight regex instead of an LLM so parsing is
    predictable and free for common project demo queries.
    """
    text = query or ""

    price_match = re.search(r"(?:under|below|less than|up to|<=?)\s*\$?(\d+(?:\.\d+)?)", text, re.I)
    if not price_match:
        price_match = re.search(r"\$(\d+(?:\.\d+)?)", text)

    max_price = float(price_match.group(1)) if price_match else None

    size_match = re.search(
        r"\b(?:size|in size)\s*([a-zA-Z0-9./-]+)\b",
        text,
        re.I,
    )
    size = size_match.group(1).upper() if size_match else None

    description = text.lower()

    # Remove price phrases.
    description = re.sub(r"(?:under|below|less than|up to|<=?)\s*\$?\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"\$\d+(?:\.\d+)?", " ", description)

    # Remove size phrases.
    description = re.sub(r"\b(?:in size|size)\s+[a-zA-Z0-9./-]+\b", " ", description)

    # Remove common conversational filler.
    filler_patterns = [
        r"\bi am looking for\b",
        r"\bi'm looking for\b",
        r"\bim looking for\b",
        r"\blooking for\b",
        r"\bi want\b",
        r"\bi need\b",
        r"\bwhat's out there\b",
        r"\bwhats out there\b",
        r"\bhow would i style it\b",
        r"\bhow do i style it\b",
    ]
    for pattern in filler_patterns:
        description = re.sub(pattern, " ", description)

    description = re.sub(r"[^a-zA-Z0-9\s-]", " ", description)
    description = re.sub(r"\s+", " ", description).strip()

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    session = _new_session(query, wardrobe)

    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    results = search_listings(description, size=size, max_price=max_price)
    session["search_results"] = results

    if not results:
        session["error"] = (
            "I couldn't find listings for that exact request. "
            "Try a broader description, a higher budget, or leaving out the size filter."
        )
        return session

    selected_item = results[0]
    session["selected_item"] = selected_item

    outfit = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit

    if not outfit or not outfit.strip():
        session["error"] = (
            "I found a listing, but I couldn't create an outfit suggestion. "
            "Try again with a fuller wardrobe or a different item."
        )
        return session

    fit_card = create_fit_card(outfit, selected_item)
    session["fit_card"] = fit_card

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
