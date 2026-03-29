from __future__ import annotations

from backend.schemas import GeneratePendingResponse


class GenerationService:
    """Coordinates batch generation without owning downstream business logic."""

    def __init__(self, *, queue_manager) -> None:
        self.queue_manager = queue_manager

    def generate_pending(self) -> GeneratePendingResponse:
        pending_records = self.queue_manager.list_by_status(status="pending")
        if not pending_records:
            return GeneratePendingResponse(
                status="no_pending_items",
                message="No pending records to process.",
                processed_count=0,
                success_count=0,
                failed_count=0,
            )

        return GeneratePendingResponse(
            status="partial_failure",
            message=(
                "Generate entry is wired, but formal card generation is not implemented yet. "
                f"Left {len(pending_records)} pending record(s) unchanged."
            ),
            processed_count=0,
            success_count=0,
            failed_count=0,
        )
