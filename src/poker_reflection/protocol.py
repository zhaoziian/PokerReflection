from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

PlayerTag = Literal["pro", "fish", "sticky", "tilt", "unknown"]
StreetName = Literal["preflop", "flop", "turn", "river"]


@dataclass(slots=True)
class TableContext:
    blind: str
    hero_stack: int
    effective_stack: int
    table_vibe: str
    hero_table_image: str = "unknown"
    session_id: str = "default-session"
    table_name: str = "default-table"
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class VillainProfile:
    seat: str
    label: str
    tags: list[PlayerTag] = field(default_factory=list)
    stack: int | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ActionRecord:
    actor: str
    action: str
    size: int | None = None
    facing: str | None = None
    note: str | None = None


@dataclass(slots=True)
class StreetRecord:
    name: StreetName
    board: list[str] = field(default_factory=list)
    hero_hand: list[str] = field(default_factory=list)
    actions: list[ActionRecord] = field(default_factory=list)
    pot_after_street: int | None = None


@dataclass(slots=True)
class HandRecord:
    context: TableContext
    hero_position: str
    villains: list[VillainProfile]
    preflop: StreetRecord
    flop: StreetRecord | None = None
    turn: StreetRecord | None = None
    river: StreetRecord | None = None
    logic_gates: list[str] = field(default_factory=list)
    hand_id: str = "default-hand"

    def ordered_streets(self) -> list[StreetRecord]:
        return [street for street in [self.preflop, self.flop, self.turn, self.river] if street is not None]

    def action_chain(self) -> list[dict[str, Any]]:
        chain: list[dict[str, Any]] = []
        for street in self.ordered_streets():
            for action in street.actions:
                chain.append(
                    {
                        "street": street.name,
                        "actor": action.actor,
                        "action": action.action,
                        "size": action.size,
                        "facing": action.facing,
                        "note": action.note,
                    }
                )
        return chain

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["action_chain"] = self.action_chain()
        return payload