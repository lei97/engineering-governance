from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    seq: int
    kind: str
    movement: str
    depot: str | None = None


def export(events: Iterable[Event]) -> list[Event]:
    ordered = sorted(events, key=lambda event: event.seq)
    return [event for event in ordered if event.kind != "note"]


def active_movements(depot: str, delivered: Iterable[Event]) -> set[str]:
    active = set()
    for event in delivered:
        if event.kind == "ship" and event.depot == depot:
            active.add(event.movement)
        elif event.kind == "void":
            active.discard(event.movement)
    return active
