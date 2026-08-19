import logging
import sys
from research_agent.app.config.config import settings

def setup_logging() -> None:
    """
    Configures standard system-wide logging.
    Suppresses excessively verbose standard logs from libraries.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Custom log formatting for CLI and microservice runtime
    log_format = "%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress verbose debug messages from standard HTTP/routing libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
