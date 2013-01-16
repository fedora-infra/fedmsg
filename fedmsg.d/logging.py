# Setup fedmsg logging.
# See the following for constraints on this format http://bit.ly/Xn1WDn
config = dict(
    logging=dict(
        version=1,
        formatters=dict(
            bare={
                "format": "%(message)s",
            },
        ),
        handlers=dict(
            console={
                "class": "logging.StreamHandler",
                "formatter": "bare",
                "level": "INFO",
                "stream": "ext://sys.stdout",
            }
        ),
        loggers=dict(
            fedmsg={
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
            moksha={
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
        ),
    ),
)
