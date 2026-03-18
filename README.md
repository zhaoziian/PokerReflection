# PokerReflection
An exploitive-poker review agent for home games, focusing on player profiling and deep-stack dynamics.

An exploit-focused poker review toolkit for live home games, centered on player profiling, deep-stack dynamics, and practical range exclusion.

## Why this project exists

PokerReflection is not trying to be a pure GTO trainer. It is meant to capture the kinds of live reads that actually matter in soft 5/10-style environments:

- table vibe (`loose`, `sticky`, `tilted`, `nitty`)
- opponent tags (`pro`, `fish`, `sticky`, `tilt`)
- deep-stack pressure and SPR context
- range-capping heuristics such as "a competent player limp-calling deep usually does not show up with AA/KK often"

## Initial backend foundation

This repository now includes two core building blocks:

1. `HandRecord` protocol dataclasses for structured hand input.
2. `RangeCapper`, a configurable exploit engine with weighted logic validation and showdown-based learning.


## Quick Start

1. Create and activate a virtual environment if you want an isolated local setup.
2. Install the project in editable mode and include the UI dependency.
3. Launch the Streamlit review app.

```bash
python -m pip install -e .[ui]
streamlit run app/streamlit_app.py
```

After the app opens, use the sidebar to set stack depth, table vibe, and session metadata, then enter the hand line on the main panel to generate a `HandRecord` JSON payload and a weighted exploit read.

### How the Bayesian learning works

`LearningEngine` tracks a lightweight Bayesian posterior for each villain. When a showdown reveals a hand that was previously discounted by the logic validator, the engine treats that as contradiction evidence and increases the villain's trap probability. When showdowns match the prior exploit read, it strengthens the non-trap side instead. Once the posterior crosses the configured threshold, the system recommends disabling strong premium-exclusion logic for that villain in future hands.

## Current modules

- **HandHistory protocol**: dataclasses for context, player tags, and full preflop-to-river action capture.
- **RangeCapper**: weighted logic validator for exploit reads such as deep-stack pro limp-call capping.
- **LearningEngine**: Bayesian showdown backtracking that updates trap probability across sessions.
- **Streamlit UI prototype**: click-first hand entry shell in `app/streamlit_app.py`.

### Example protocol

```python
from poker_reflection import ActionRecord, HandRecord, StreetRecord, TableContext, VillainProfile

hand = HandRecord(
    context=TableContext(
        blind="5/10",
        hero_stack=2000,
        effective_stack=2000,
        table_vibe="loose",
        hero_table_image="wild",
        session_id="2026-03-18-evening",
        table_name="student-home-game",
        notes=["New table", "Multiple limp pots preflop"],
    ),
    hero_position="BTN",
    villains=[
        VillainProfile(
            seat="HJ",
            label="Villain 1",
            tags=["pro", "sticky"],
            stack=2100,
            notes=["Limp-calls wide", "Rarely shows premiums passively"],
        )
    ],
    preflop=StreetRecord(
        name="preflop",
        hero_hand=["Ks", "9s"],
        actions=[
            ActionRecord(actor="HJ", action="limp"),
            ActionRecord(actor="BTN", action="iso-raise", size=40),
            ActionRecord(actor="HJ", action="call", size=40, facing="iso-raise"),
        ],
        pot_after_street=95,
    ),
    logic_gates=["range_cap_enabled"],
    hand_id="hand-42",
)
```

### Example logic validator

```python
from poker_reflection import RangeCapper

capper = RangeCapper()
result = capper.apply(
    base_range={"AA", "KK", "QQ", "AKo", "KJs", "76s", "88"},
    villain_tags={"pro"},
    preflop_line="limp-call",
    effective_stack=2000,
    villain_id="hj-reg",
    is_home_game=True,
)

print(result.weighted_range["AA"])
# 0.525 in a home game instead of 0.05 in a tougher environment

update = capper.update_on_showdown(villain_id="hj-reg", actual_hand="AA")
print(update.learned_tags)
# {'tricky', 'trapper'}
```

## Next suggested layers

- **StackAdvisor**: connect SPR bands to sizing advice.
- **ImageTracker**: estimate how your recent bluff frequency changes call-down behavior.
- **Streamlit input UI**: optimize for click-heavy hand capture with a "mark this pot" shortcut.
- **Custom logic library**: let users override exclusions by player pool or villain archetype.

## Development

```bash
python -m pytest
```


## Streamlit prototype

Run the click-first demo UI with:

```bash
streamlit run app/streamlit_app.py
```

## Learning example

```python
from poker_reflection import LearningEngine

engine = LearningEngine()
feedback = engine.record_showdown(
    villain_id="hj-reg",
    session_id="2026-03-18-evening",
    hand_id="hand-42",
    action_signature="limp-call",
    actual_hand="AA",
    discounted_combos={"AA": 0.05, "KK": 0.05},
    villain_tags={"pro"},
)

print(feedback.trap_probability)
print(feedback.recommended_disable_strong_exclusions)
```
