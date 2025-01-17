import logging

admin_id=767394443820662784

# Configure logger
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="data/bot.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

