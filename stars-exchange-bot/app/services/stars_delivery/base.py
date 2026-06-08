from dataclasses import dataclass


@dataclass
class DeliveryResult:
    ok: bool
    requires_manual: bool = False
    error: str | None = None
    delivered_stars: int | None = None
