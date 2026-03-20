import sys
from loguru import logger

from .config import settings
from .fetcher import FetcherService


def main() -> None:
    mode = settings.MODE.lower()
    if mode == "fetcher":
        logger.info("Running in FETCHER mode")
        service = FetcherService()
        service.run()
    elif mode == "publisher":
        logger.info("Running in PUBLISHER mode")
        # PublisherService will be implemented later
        logger.warning("Publisher mode is not yet implemented.")
        sys.exit(0)
    else:
        logger.error(f"Unknown mode: {mode}. Please set MODE to 'fetcher' or 'publisher'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
