import logging
import dotenv
import os

#### ---------- LOGGING ---------- ####
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_credentials():
    """
    Load credentials from environment variables.
    
    RETURNS:
        dict: A dictionary containing the credentials.
    
    RAISES:
        Exception: If there is an error loading the environment variables.
    """
    try:
        dotenv.load_dotenv()
        logger.info("🔄 Loading environment variables...")

        return {
            "EMAIL": os.getenv("RENDER_EMAIL"),
            "PASSWORD": os.getenv("RENDER_PASSWORD")
        }
    except Exception as e:
        logger.error(f"❌ Error loading environment variables: {e}")
        raise
