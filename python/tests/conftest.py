import pytest
import logging

# Additional test fixtures can be added here

@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for tests."""
    for logger_name in [
        'autogen.import_utils',
        'httpcore',
        'httpx',
        'asyncio',
        'grpc',
        'openai',
        'anthropic'
    ]:
        logging.getLogger(logger_name).setLevel(logging.INFO)
    
    # Completely suppress import errors
    class ImportErrorFilter(logging.Filter):
        def filter(self, record):
            return "ImportError" not in record.getMessage()
    
    # Apply the filter
    for handler in logging.getLogger().handlers:
        handler.addFilter(ImportErrorFilter())
