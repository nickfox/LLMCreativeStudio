import logging
import pytest

def pytest_configure(config):
    """
    Configure logging levels before tests run.
    """
    # Silence unnecessary warnings
    logging.getLogger('autogen.import_utils').setLevel(logging.INFO)
    logging.getLogger('httpcore').setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.INFO)
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.getLogger('grpc').setLevel(logging.INFO)
    
    # Add a filter to suppress certain warning messages
    class ImportWarningFilter(logging.Filter):
        def filter(self, record):
            if "Ignoring ImportError:" in record.getMessage():
                return False
            return True

    # Apply the filter to the root logger
    root_logger = logging.getLogger()
    root_logger.addFilter(ImportWarningFilter())
