from poker_reflection import ActionRecord, HandRecord, StreetRecord, TableContext, VillainProfile


class TestProtocol:
    def test_hand_record_serializes_flat_action_chain(self) -> None:
        hand = HandRecord(
            hand_id="hand-1",
            context=TableContext(
                blind="5/10",
                hero_stack=2000,
                effective_stack=1800,
                table_vibe="loose",
                session_id="session-a",
                table_name="student-home-game",
            ),
            hero_position="BTN",
            villains=[VillainProfile(seat="HJ", label="Villain", tags=["pro"])],
            preflop=StreetRecord(
                name="preflop",
                hero_hand=["As", "Kd"],
                actions=[
                    ActionRecord(actor="HJ", action="limp"),
                    ActionRecord(actor="BTN", action="iso-raise", size=40),
                ],
            ),
            flop=StreetRecord(
                name="flop",
                board=["Ah", "8d", "4c"],
                actions=[ActionRecord(actor="BTN", action="bet", size=65)],
            ),
        )

        payload = hand.to_dict()

        assert payload["hand_id"] == "hand-1"
        assert payload["context"]["session_id"] == "session-a"
        assert payload["context"]["table_name"] == "student-home-game"
        assert payload["action_chain"] == [
            {
                "street": "preflop",
                "actor": "HJ",
                "action": "limp",
                "size": None,
                "facing": None,
                "note": None,
            },
            {
                "street": "preflop",
                "actor": "BTN",
                "action": "iso-raise",
                "size": 40,
                "facing": None,
                "note": None,
            },
            {
                "street": "flop",
                "actor": "BTN",
                "action": "bet",
                "size": 65,
                "facing": None,
                "note": None,
            },
        ]