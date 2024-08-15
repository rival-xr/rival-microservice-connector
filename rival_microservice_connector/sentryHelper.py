import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

def configure_sentry(dsn, env):
  sentry_sdk.init(
    dsn=dsn,
    integrations=[LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)],
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=env
  )