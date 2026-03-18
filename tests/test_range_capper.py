from poker_reflection import RangeCapper


class TestRangeCapper:
    def test_pro_limp_call_discounted_to_weighted_probabilities(self) -> None:
        capper = RangeCapper()
        result = capper.apply(
            base_range={"AA", "KK", "AKo", "88", "76s", "KJs"},
            villain_tags={"pro"},
            preflop_line="limp-call",
            effective_stack=2000,
            villain_id="villain-1",
        )

        assert result.weighted_range["AA"] == 0.05
        assert result.weighted_range["KK"] == 0.05
        assert result.weighted_range["AKo"] == 0.15
        assert result.weighted_range["88"] == 0.20
        assert result.weighted_range["76s"] == 1.0
        assert result.discounted_combos == {
            "AA": 0.05,
            "KK": 0.05,
            "AKo": 0.15,
            "88": 0.2,
        }
        assert any("discounted the top of range" in reason for reason in result.reasons)

    def test_home_game_halves_elimination_weight(self) -> None:
        capper = RangeCapper()
        result = capper.apply(
            base_range={"AA", "KK", "76s"},
            villain_tags={"pro"},
            preflop_line="limp-call",
            effective_stack=2000,
            villain_id="villain-1",
            is_home_game=True,
        )

        assert result.weighted_range["AA"] == 0.525
        assert result.weighted_range["KK"] == 0.525
        assert result.weighted_range["76s"] == 1.0

    def test_showdown_learning_disables_future_premium_discounting(self) -> None:
        capper = RangeCapper()
        initial_result = capper.apply(
            base_range={"AA", "KK", "76s"},
            villain_tags={"pro"},
            preflop_line="limp-call",
            effective_stack=2000,
            villain_id="villain-42",
        )
        assert initial_result.weighted_range["AA"] == 0.05

        update = capper.update_on_showdown(villain_id="villain-42", actual_hand="AA")
        assert update.triggered_learning is True
        assert update.learned_tags == {"tricky", "trapper"}

        follow_up = capper.apply(
            base_range={"AA", "KK", "76s"},
            villain_tags={"pro"},
            preflop_line="limp-call",
            effective_stack=2000,
            villain_id="villain-42",
        )

        assert follow_up.weighted_range == {"AA": 1.0, "KK": 1.0, "76s": 1.0}
        assert follow_up.discounted_combos == {}
        assert follow_up.learned_tags == {"pro", "tricky", "trapper"}
        assert any("tricky/trapper" in reason for reason in follow_up.reasons)