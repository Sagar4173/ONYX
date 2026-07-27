import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self):
        self.sentry_initialized = False
        self.prometheus_instrumentor: Optional["Instrumentator"] = None

    def init_sentry(self, dsn: str, environment: str = "development"):
        if not dsn:
            logger.warning("No Sentry DSN configured -- skipping Sentry initialization")
            return

        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.2,
            send_default_pii=False,
            attach_stacktrace=True,
        )
        self.sentry_initialized = True
        logger.info("Sentry error tracking initialized")

    def init_prometheus(self, app):
        if not app:
            logger.warning("No FastAPI app provided -- skipping Prometheus initialization")
            return

        from prometheus_fastapi_instrumentator import Instrumentator

        self.prometheus_instrumentor = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
        )
        self.prometheus_instrumentor.instrument(app).expose(app, endpoint="/metrics")
        logger.info("Prometheus metrics exposed at /metrics")
