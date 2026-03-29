from __future__ import annotations

from backend.schemas import GeneratePendingResponse


class GenerationService:
    """Coordinates batch generation without owning downstream business logic."""

    def __init__(self, *, queue_manager, single_generation_service) -> None:
        self.queue_manager = queue_manager
        self.single_generation_service = single_generation_service

    def generate_pending(self) -> GeneratePendingResponse:
        pending_record = self.queue_manager.get_oldest_pending()
        if pending_record is None:
            return GeneratePendingResponse(
                status="no_pending_items",
                message="No pending records to process.",
                processed_count=0,
                success_count=0,
                failed_count=0,
            )

        result = self.single_generation_service.generate(pending_record)
        self.queue_manager.update_status(
            record_id=result.record_id,
            status=result.status,
            error_message=result.error_message,
        )

        if result.status == "success":
            return GeneratePendingResponse(
                status="processed_one_success",
                message=f"Processed pending record '{result.word_key}' successfully.",
                processed_count=1,
                success_count=1,
                failed_count=0,
                record_id=result.record_id,
                word_key=result.word_key,
            )

        return GeneratePendingResponse(
            status="processed_one_failed",
            message=(
                f"Failed to process pending record '{result.word_key}': "
                f"{result.error_message}"
            ),
            processed_count=1,
            success_count=0,
            failed_count=1,
            record_id=result.record_id,
            word_key=result.word_key,
            error_message=result.error_message,
        )

    def generate_all_pending(self) -> GeneratePendingResponse:
        processed_count = 0
        success_count = 0
        failed_count = 0

        while True:
            response = self.generate_pending()
            if response.status == "no_pending_items":
                if processed_count == 0:
                    return response
                break

            processed_count += response.processed_count
            success_count += response.success_count
            failed_count += response.failed_count

        if failed_count == 0:
            return GeneratePendingResponse(
                status="processed_all_success",
                message="Processed all pending records successfully.",
                processed_count=processed_count,
                success_count=success_count,
                failed_count=failed_count,
            )

        return GeneratePendingResponse(
            status="processed_all_with_failures",
            message="Processed all pending records with failures.",
            processed_count=processed_count,
            success_count=success_count,
            failed_count=failed_count,
        )
