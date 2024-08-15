import logging
import sys

class _InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)

def configure_logging(level=logging.INFO):
  outHandler = logging.StreamHandler(sys.stdout)
  outHandler.addFilter(_InfoFilter())

  errHandler = logging.StreamHandler()
  errHandler.setLevel(logging.WARNING)

  logging.basicConfig(
      level=level,
      format='%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s',
      handlers=[outHandler, errHandler]
)
