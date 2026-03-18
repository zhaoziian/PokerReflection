from __future__ import annotations

import json

import streamlit as st

from poker_reflection import (
    ActionRecord,
    HandRecord,
    LearningEngine,
    RangeCapper,
    StreetRecord,
    TableContext,
    VillainProfile,
)

st.set_page_config(page_title="PokerReflection", layout="wide")
st.title("PokerReflection")
st.caption("Click-first exploit review for deep-stack live games.")

with st.sidebar:
    st.header("Table Context")
    blind = st.selectbox("Blind", ["1/3", "2/5", "5/10", "10/20"], index=2)
    hero_stack = st.number_input("Hero Stack", min_value=100, value=2000, step=50)
    effective_stack = st.number_input("Effective Stack", min_value=100, value=2000, step=50)
    table_vibe = st.selectbox("Table Vibe", ["Loose", "Sticky", "Tilted", "Nitty"], index=0)
    hero_image = st.selectbox("Hero Image", ["Unknown", "Wild", "Solid", "Nit", "Splashy"], index=1)
    is_home_game = st.toggle("Home Game Mode", value=True)
    session_id = st.text_input("Session ID", value="2026-03-18-night")
    table_name = st.text_input("Table Name", value="student-home-game")

st.subheader("Hand Builder")
left, right = st.columns(2)
with left:
    hero_position = st.selectbox("Hero Position", ["UTG", "HJ", "CO", "BTN", "SB", "BB"], index=3)
    hero_cards = st.text_input("Hero Hand", value="Ks 9s")
    villain_label = st.text_input("Villain Label", value="HJ Reg")
    villain_seat = st.selectbox("Villain Seat", ["UTG", "HJ", "CO", "BTN", "SB", "BB"], index=1)
    villain_tags = st.multiselect(
        "Villain Tags",
        ["pro", "fish", "sticky", "tilt", "unknown"],
        default=["pro", "sticky"],
    )
with right:
    preflop_line = st.selectbox("Preflop Read", ["limp-call", "cold-call-3bet", "raise-call", "unknown"], index=0)
    iso_size = st.number_input("Iso / Open Size", min_value=0, value=40, step=5)
    flop_cards = st.text_input("Flop", value="Kh 8d 4c")
    flop_bet = st.number_input("Hero Flop Bet", min_value=0, value=150, step=25)
    flop_raise = st.number_input("Villain Raise", min_value=0, value=400, step=25)

hand = HandRecord(
    context=TableContext(
        blind=blind,
        hero_stack=hero_stack,
        effective_stack=effective_stack,
        table_vibe=table_vibe.lower(),
        hero_table_image=hero_image.lower(),
        session_id=session_id,
        table_name=table_name,
        notes=["Built from Streamlit click UI prototype"],
    ),
    hero_position=hero_position,
    villains=[
        VillainProfile(
            seat=villain_seat,
            label=villain_label,
            tags=villain_tags or ["unknown"],
            stack=effective_stack,
            notes=[f"Primary preflop line: {preflop_line}"],
        )
    ],
    preflop=StreetRecord(
        name="preflop",
        hero_hand=hero_cards.split(),
        actions=[
            ActionRecord(actor=villain_seat, action=preflop_line.split("-")[0]),
            ActionRecord(actor=hero_position, action="iso-raise", size=iso_size),
            ActionRecord(actor=villain_seat, action="call", size=iso_size, facing="iso-raise"),
        ],
        pot_after_street=iso_size * 2 + 15,
    ),
    flop=StreetRecord(
        name="flop",
        board=flop_cards.split(),
        actions=[
            ActionRecord(actor=hero_position, action="bet", size=flop_bet),
            ActionRecord(actor=villain_seat, action="raise", size=flop_raise, facing="bet"),
        ],
    ),
    logic_gates=["range_cap_enabled", "learning_engine_ready"],
    hand_id="demo-hand-001",
)

range_capper = RangeCapper()
learning_engine = LearningEngine()
sample_range = {"AA", "KK", "QQ", "AKo", "KJs", "76s", "88"}
analysis = range_capper.apply(
    base_range=sample_range,
    villain_tags=set(villain_tags),
    preflop_line=preflop_line,
    effective_stack=effective_stack,
    villain_id=villain_label,
    is_home_game=is_home_game,
)

json_col, analysis_col = st.columns(2)
with json_col:
    st.markdown("#### HandHistory JSON")
    st.code(json.dumps(hand.to_dict(), indent=2), language="json")

with analysis_col:
    st.markdown("#### Logic Validator")
    st.write("Weighted range", analysis.weighted_range)
    st.write("Reasons", analysis.reasons)
    showdown_hand = st.selectbox("Record Showdown", ["AA", "KK", "QQ", "AKo", "KJs", "76s", "88"])
    if st.button("Apply Showdown Learning"):
        feedback = learning_engine.record_showdown(
            villain_id=villain_label,
            session_id=session_id,
            hand_id=hand.hand_id,
            action_signature=preflop_line,
            actual_hand=showdown_hand,
            discounted_combos=analysis.discounted_combos,
            villain_tags=set(villain_tags),
        )
        st.success(
            f"Trap probability={feedback.trap_probability:.2f}, learned tags={sorted(feedback.learned_tags)}"
        )