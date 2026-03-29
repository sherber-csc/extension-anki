from __future__ import annotations


class GenerationService:
    """Coordinates batch generation without owning downstream business logic."""

    def generate_pending(self) -> None:
        raise NotImplementedError("Batch generation is implemented in a later phase.")
