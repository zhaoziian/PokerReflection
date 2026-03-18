from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RangeCapConfig:
    pro_limp_call_weights: dict[str, float] = field(
        default_factory=lambda: {
            "AA": 0.05,
            "KK": 0.05,
            "QQ": 0.10,
            "AKs": 0.15,
            "AKo": 0.15,
            "88": 0.20,
        }
    )
    fish_limp_call_weights: dict[str, float] = field(default_factory=dict)
    sticky_cold_call_3bet_weights: dict[str, float] = field(
        default_factory=lambda: {"AA": 0.15, "KK": 0.15}
    )


@dataclass(slots=True)
class VillainLogicProfile:
    learned_tags: set[str] = field(default_factory=set)
    disable_strong_exclusions: bool = False


@dataclass(slots=True)
class RangeCapResult:
    input_range: set[str]
    weighted_range: dict[str, float]
    discounted_combos: dict[str, float]
    reasons: list[str]
    learned_tags: set[str]


@dataclass(slots=True)
class ShowdownUpdateResult:
    villain_id: str
    actual_hand: str
    triggered_learning: bool
    learned_tags: set[str]
    notes: list[str]


class RangeCapper:
    """Apply exploit-driven range weights from live-read heuristics.

    Instead of hard-removing combos, the logic validator discounts them with
    probabilities. It can also learn from showdown evidence: if a villain shows
    up with a hand that was heavily discounted, that villain is marked as a
    trap-capable player and future premium exclusions are disabled.
    """

    def __init__(self, config: RangeCapConfig | None = None) -> None:
        self.config = config or RangeCapConfig()
        self._villain_profiles: dict[str, VillainLogicProfile] = {}
        self._last_discounted: dict[str, set[str]] = {}

    def apply(
        self,
        *,
        base_range: set[str],
        villain_tags: set[str],
        preflop_line: str,
        effective_stack: int,
        villain_id: str = "default",
        has_trap_note: bool = False,
        is_home_game: bool = False,
    ) -> RangeCapResult:
        profile = self._villain_profiles.setdefault(villain_id, VillainLogicProfile())
        learned_tags = set(villain_tags) | profile.learned_tags
        weighted_range = {combo: 1.0 for combo in base_range}
        reasons: list[str] = []

        if has_trap_note:
            reasons.append("Trap note present: skipped probability discounting for premium traps.")
            self._last_discounted[villain_id] = set()
            return self._build_result(base_range, weighted_range, reasons, learned_tags)

        if profile.disable_strong_exclusions:
            reasons.append(
                "Showdown learning marked villain as tricky/trapper; premium exclusion logic disabled."
            )
            self._last_discounted[villain_id] = set()
            return self._build_result(base_range, weighted_range, reasons, learned_tags)

        if preflop_line == "limp-call" and "pro" in learned_tags and effective_stack >= 1000:
            self._apply_weight_map(
                weighted_range,
                self.config.pro_limp_call_weights,
                is_home_game=is_home_game,
            )
            if any(combo in self.config.pro_limp_call_weights for combo in base_range):
                reasons.append(
                    "Deep-stack pro limp-call validator discounted the top of range "
                    "without removing trap combos entirely."
                )

        if preflop_line == "limp-call" and "fish" in learned_tags:
            self._apply_weight_map(
                weighted_range,
                self.config.fish_limp_call_weights,
                is_home_game=is_home_game,
            )
            if any(combo in self.config.fish_limp_call_weights for combo in base_range):
                reasons.append("Fish limp-call validator applied configured probability discounts.")

        if preflop_line == "cold-call-3bet" and "sticky" in learned_tags:
            self._apply_weight_map(
                weighted_range,
                self.config.sticky_cold_call_3bet_weights,
                is_home_game=is_home_game,
            )
            if any(combo in self.config.sticky_cold_call_3bet_weights for combo in base_range):
                reasons.append("Sticky cold-call 3-bet validator discounted slow-play premiums.")

        if not reasons:
            reasons.append("No exploit-specific validator matched; range left at baseline probabilities.")

        return self._build_result(base_range, weighted_range, reasons, learned_tags, villain_id)

    def update_on_showdown(self, *, villain_id: str = "default", actual_hand: str) -> ShowdownUpdateResult:
        profile = self._villain_profiles.setdefault(villain_id, VillainLogicProfile())
        discounted = self._last_discounted.get(villain_id, set())
        notes: list[str] = []
        triggered_learning = actual_hand in discounted

        if triggered_learning:
            profile.learned_tags.update({"tricky", "trapper"})
            profile.disable_strong_exclusions = True
            notes.append(
                "Observed a discounted combo at showdown; villain marked tricky/trapper and future premium caps disabled."
            )
        else:
            notes.append("Showdown hand did not contradict the active validator.")

        return ShowdownUpdateResult(
            villain_id=villain_id,
            actual_hand=actual_hand,
            triggered_learning=triggered_learning,
            learned_tags=set(profile.learned_tags),
            notes=notes,
        )

    def _build_result(
        self,
        base_range: set[str],
        weighted_range: dict[str, float],
        reasons: list[str],
        learned_tags: set[str],
        villain_id: str | None = None,
    ) -> RangeCapResult:
        discounted_combos = {
            combo: weight for combo, weight in weighted_range.items() if weight < 1.0
        }
        if villain_id is not None:
            self._last_discounted[villain_id] = set(discounted_combos)
        return RangeCapResult(
            input_range=set(base_range),
            weighted_range=weighted_range,
            discounted_combos=discounted_combos,
            reasons=reasons,
            learned_tags=learned_tags,
        )

    @staticmethod
    def _apply_weight_map(
        weighted_range: dict[str, float],
        configured_weights: dict[str, float],
        *,
        is_home_game: bool,
    ) -> None:
        for combo, keep_probability in configured_weights.items():
            if combo not in weighted_range:
                continue

            adjusted_keep_probability = keep_probability
            if is_home_game:
                elimination_share = 1.0 - keep_probability
                adjusted_keep_probability = 1.0 - (elimination_share / 2.0)

            weighted_range[combo] = min(weighted_range[combo], round(adjusted_keep_probability, 4))