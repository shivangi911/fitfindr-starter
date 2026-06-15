from tools import search_listings, suggest_outfit, create_fit_card


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe():
    item = {
        "title": "Vintage Graphic Tee",
        "description": "Soft faded band tee",
        "category": "tops",
        "style_tags": ["vintage", "casual"],
        "colors": ["black"],
        "price": 22,
        "platform": "Depop",
    }
    result = suggest_outfit(item, {"items": []})
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_create_fit_card_missing_outfit():
    item = {"title": "Vintage Graphic Tee", "price": 22, "platform": "Depop"}
    result = create_fit_card("", item)
    assert "Unable to create fit card" in result
