from app.application.health.schemas import HealthStatus
from app.core.settings import Settings


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_status(self) -> HealthStatus:
        return HealthStatus(
            status="ok",
            service=self._settings.app_name,
            environment=self._settings.app_env,
        )

