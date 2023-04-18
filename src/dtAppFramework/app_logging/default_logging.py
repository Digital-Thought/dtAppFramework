def default_config(log_level="INFO"):
    return {
        "version": 1,
        "formatters": {
            "simple_file": {
                "format": "%(asctime)s - %(levelname)s - %(processName)s.%(process)d - %(threadName)s.%(thread)d - %(module)s.%(funcName)s.%(lineno)d - %(message)s"
            },
            "elastic": {
                "format": "ELASTIC: %(asctime)s - %(levelname)s - %(processName)s.%(process)d - %(threadName)s.%(thread)d - %(module)s.%(funcName)s.%(lineno)d - %(message)s"
            }
        },
        "handlers": {
            "logfile_ALL": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "DEBUG",
                "formatter": "simple_file",
                "filename": "",
                "when": "D",
                "interval": 1,
                "encoding": "utf8"
            },
            "logfile_ERR": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "ERROR",
                "formatter": "simple_file",
                "filename": "",
                "when": "D",
                "interval": 1,
                "encoding": "utf8"
            },
            "logfile_ELASTIC": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "DEBUG",
                "formatter": "simple_file",
                "filename": "",
                "when": "D",
                "interval": 1,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "defaultLogger": {
                "level": log_level,
                "handlers": [
                    "logfile_ALL",
                    "logfile_ERR"
                ],
                "propagate": "no"
            },
            "elasticsearch": {
                "level": log_level,
                "handlers": [
                    "logfile_ELASTIC"
                ],
                "propagate": "no"
            },
            "elastic": {
                "level": log_level,
                "handlers": [
                    "logfile_ELASTIC"
                ],
                "propagate": "no"
            }
        },
        "root": {
            "level": log_level,
            "handlers": [
                "logfile_ALL",
                "logfile_ERR"
            ]
        }
    }
