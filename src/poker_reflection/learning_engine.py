from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ShowdownFeedback:
    villain_id: str
    session_id: str
    hand_id: str
    action_signature: str
    actual_hand: str
    contradicted_discount: bool
    trap_probability: float
    learned_tags: set[str]
    recommended_disable_strong_exclusions: bool


@dataclass(slots=True)
class VillainPosterior:
    trap_alpha: float = 1.0
    trap_beta: float = 3.0
    learned_tags: set[str] = field(default_factory=set)
    hands_observed: int = 0
    contradictions_seen: int = 0
    history: list[ShowdownFeedback] = field(default_factory=list)

    @property
    def trap_probability(self) -> float:
        return self.trap_alpha / (self.trap_alpha + self.trap_beta)


class LearningEngine:
    """Bayesian showdown backtracking for cross-session villain adaptation."""

    def __init__(self, *, trap_threshold: float = 0.4) -> None:
        self.trap_threshold = trap_threshold
        self._profiles: dict[str, VillainPosterior] = {}

    def record_showdown(
        self,
        *,
        villain_id: str,
        session_id: str,
        hand_id: str,
        action_signature: str,
        actual_hand: str,
        discounted_combos: dict[str, float],
        villain_tags: set[str] | None = None,
    ) -> ShowdownFeedback:
        profile = self._profiles.setdefault(villain_id, VillainPosterior())
        contradicted_discount = actual_hand in discounted_combos
        profile.hands_observed += 1

        if contradicted_discount:
            profile.trap_alpha += 1.0
            profile.contradictions_seen += 1
            profile.learned_tags.update({"tricky", "trapper"})
        else:
            profile.trap_beta += 1.0

        if villain_tags:
            profile.learned_tags.update(villain_tags)

        feedback = ShowdownFeedback(
            villain_id=villain_id,
            session_id=session_id,
            hand_id=hand_id,
            action_signature=action_signature,
            actual_hand=actual_hand,
            contradicted_discount=contradicted_discount,
            trap_probability=round(profile.trap_probability, 4),
            learned_tags=set(profile.learned_tags),
            recommended_disable_strong_exclusions=profile.trap_probability >= self.trap_threshold,
        )
        profile.history.append(feedback)
        return feedback

    def get_profile(self, villain_id: str) -> VillainPosterior:
        return self._profiles.setdefault(villain_id, VillainPosterior())