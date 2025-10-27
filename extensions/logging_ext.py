import logging


logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] [%(filename)s] [%(asctime)s]: %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S')

log = logging.getLogger(__name__)