# PokerReflection

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