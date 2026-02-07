from dataclasses import dataclass


@dataclass
class ConnpassEvent:
    id: int
    title: str
    catch: str | None
    description: str | None
    url: str
    started_at: str | None
    ended_at: str | None
    place: str | None
    address: str | None
    accepted: int
    waiting: int
    limit: int | None
    event_type: str
    open_status: str


@dataclass
class ConnpassSearchResult:
    results_returned: int
    results_available: int
    results_start: int
    events: list[ConnpassEvent]
