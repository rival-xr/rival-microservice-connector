import logging
import sys

class _OutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.ERROR, logging.INFO)

def configure_logging():
  outHandler = logging.StreamHandler(sys.stdout)
  outHandler.addFilter(_OutFilter())

  errHandler = logging.StreamHandler()
  errHandler.setLevel(logging.WARNING)

  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s',
      handlers=[outHandler, errHandler]
)
