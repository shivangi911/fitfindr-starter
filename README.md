# FitFindr

## Overview

FitFindr is a multi-tool AI agent that helps users discover secondhand clothing items, style them with an existing wardrobe, and generate social-media-ready outfit captions. The agent combines search, reasoning, and content generation by orchestrating multiple tools and passing information between them through a shared session state.

The project demonstrates tool orchestration, planning loops, state management, error handling, and LLM integration using Groq's `llama-3.3-70b-versatile` model.

---

# Tool Inventory

## 1. search_listings(description, size, max_price)

### Purpose

Searches the mock secondhand listings dataset and returns the most relevant items matching the user's request.

### Inputs

* `description (str)` – Clothing description or style requested by the user.
* `size (str | None)` – Desired clothing size.
* `max_price (float | None)` – Maximum budget.

### Output

* `list[dict]` containing matching listings sorted by relevance.

### Example Return Value

```python
[
    {
        "title": "Y2K Baby Tee — Butterfly Print",
        "price": 18.0,
        "platform": "Depop",
        ...
    }
]
```

---

## 2. suggest_outfit(new_item, wardrobe)

### Purpose

Generates one or more outfit ideas using the selected thrift item and the user's wardrobe.

### Inputs

* `new_item (dict)` – Listing selected from search results.
* `wardrobe (dict)` – User wardrobe object.

### Output

* `str` containing one or more complete outfit suggestions.

### Example Output

```text
Pair the baby tee with baggy jeans and chunky sneakers for a casual Y2K look.
```

---

## 3. create_fit_card(outfit, new_item)

### Purpose

Creates a short social-media-style outfit caption based on the generated outfit suggestion.

### Inputs

* `outfit (str)` – Outfit recommendation.
* `new_item (dict)` – Selected thrift item.

### Output

* `str` containing a shareable outfit caption.

### Example Output

```text
Just scored this Y2K baby tee on Depop for $18 and I'm obsessed.
```

---

# Planning Loop

The agent uses a conditional planning loop rather than calling all tools unconditionally.

1. Parse the user query into:

   * description
   * size
   * max_price

2. Call:

```python
search_listings(description, size, max_price)
```

3. Check search results:

   * If results are empty:

     * Set `session["error"]`
     * Return immediately
   * Otherwise:

     * Store the top result in `session["selected_item"]`

4. Call:

```python
suggest_outfit(selected_item, wardrobe)
```

5. Store the returned outfit in:

```python
session["outfit_suggestion"]
```

6. Call:

```python
create_fit_card(outfit_suggestion, selected_item)
```

7. Store the result in:

```python
session["fit_card"]
```

8. Return the completed session.

This means the agent behaves differently depending on what previous tools return. If no listings are found, the workflow terminates early and later tools are not called.

---

# State Management

The project uses a shared session dictionary to maintain state across tool calls.

### Stored Session Fields

* `query`
* `parsed`
* `search_results`
* `selected_item`
* `wardrobe`
* `outfit_suggestion`
* `fit_card`
* `error`

### State Flow

```text
User Query
    ↓
search_listings
    ↓
selected_item
    ↓
suggest_outfit
    ↓
outfit_suggestion
    ↓
create_fit_card
    ↓
fit_card
```

Information returned by one tool is stored in the session and reused by later tools without requiring the user to re-enter information.

---

# Error Handling Strategy

## search_listings

### Failure Mode

No matching listings are found.

### Response

Returns an empty list.

### Agent Behavior

```text
I couldn't find listings for that exact request.
Try a broader description, a higher budget,
or leaving out the size filter.
```

The planning loop stops immediately and does not call the remaining tools.

---

## suggest_outfit

### Failure Mode

User wardrobe is empty.

### Response

Generates a general styling suggestion using common wardrobe staples.

### Additional Protection

If the Groq request fails, a fallback outfit suggestion is generated from the listing details.

---

## create_fit_card

### Failure Mode

Outfit information is missing.

### Response

```text
Unable to create fit card because outfit information is missing.
```

### Additional Protection

If the Groq request fails, a fallback caption is generated using the item information.

---

# Testing

The project includes pytest tests covering tool behavior and failure cases.

### Tested Scenarios

* Search returns valid results
* Search returns no results
* Price filtering works correctly
* Empty wardrobe handling
* Missing outfit handling

Example command:

```bash
PYTHONPATH=. pytest tests/
```

Result:

```text
5 passed
```

---

# Spec Reflection

The planning specification helped define tool interfaces, session state, planning logic, and failure handling before implementation. Having a clear specification made it easier to verify that the generated code matched the intended behavior.

One implementation difference from the original specification was the addition of fallback responses for Groq failures. Instead of terminating when the LLM is unavailable, the agent generates simple backup responses so that the workflow remains usable.

---

# AI Usage

## Instance 1 – Tool Implementation

I used ChatGPT to implement `search_listings()` using the tool specification defined in `planning.md`.

Inputs provided:

* Tool purpose
* Input parameters
* Expected return value
* Failure mode

Before using the generated code, I verified that:

* Filtering worked for description, size, and price
* Results were sorted by relevance
* Empty searches returned an empty list rather than raising exceptions

---

## Instance 2 – Planning Loop

I used ChatGPT to help implement the planning loop in `agent.py`.

Inputs provided:

* Planning Loop section from `planning.md`
* State Management section
* Architecture diagram

Before using the generated code, I verified that:

* The agent branches when no search results are found
* State is stored in the session dictionary
* The selected item is passed into `suggest_outfit`
* The outfit suggestion is passed into `create_fit_card`
* The agent does not call all tools unconditionally

---

# Demo

The demo video demonstrates:

1. A complete interaction using:

   * `search_listings`
   * `suggest_outfit`
   * `create_fit_card`

2. State passing between tools.

3. A triggered failure scenario where no matching listings are found.

4. The agent's graceful error handling and recovery behavior.

---

# Technologies Used

* Python
* Groq API
* llama-3.3-70b-versatile
* Gradio
* Pytest
* JSON
