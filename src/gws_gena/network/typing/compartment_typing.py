from typing import TypedDict


class CompartmentDict(TypedDict):
    id: str | None
    go_id: str | None
    bigg_id: str | None
    name: str | None
    color: str | None
    is_steady: bool | None
