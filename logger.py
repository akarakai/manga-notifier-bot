import logging

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name) 
    logger.setLevel(logging.INFO)

    if not logger.handlers:  
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
