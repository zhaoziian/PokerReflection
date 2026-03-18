from poker_reflection import LearningEngine


class TestLearningEngine:
    def test_record_showdown_increases_trap_probability_on_contradiction(self) -> None:
        engine = LearningEngine(trap_threshold=0.4)
        feedback = engine.record_showdown(
            villain_id="villain-1",
            session_id="session-a",
            hand_id="hand-1",
            action_signature="limp-call",
            actual_hand="AA",
            discounted_combos={"AA": 0.05, "KK": 0.05},
            villain_tags={"pro"},
        )

        assert feedback.contradicted_discount is True
        assert feedback.trap_probability == 0.4
        assert feedback.learned_tags == {"pro", "tricky", "trapper"}
        assert feedback.recommended_disable_strong_exclusions is True

    def test_record_showdown_strengthens_non_trap_prior_when_read_holds(self) -> None:
        engine = LearningEngine(trap_threshold=0.5)
        feedback = engine.record_showdown(
            villain_id="villain-2",
            session_id="session-a",
            hand_id="hand-2",
            action_signature="limp-call",
            actual_hand="76s",
            discounted_combos={"AA": 0.05, "KK": 0.05},
            villain_tags={"fish"},
        )

        assert feedback.contradicted_discount is False
        assert feedback.trap_probability == 0.2
        assert feedback.learned_tags == {"fish"}
        assert feedback.recommended_disable_strong_exclusions is False