import logging
from snowballing.config import config

logging.basicConfig(format=config["logging"]["format"])

logging.getLogger().setLevel(logging.FATAL)  # disable imported module logs

# to be imported ...
log = logging.getLogger("scholarsemantic")

log.setLevel(config["logging"]["level"])

log.addHandler(logging.FileHandler(config["logging"]["log-file"]))
for log_handler in log.handlers:
    log_handler.setFormatter(logging.Formatter(config["logging"]["format"]))