import logging

# Configure logging to suppress DEBUG messages from autogen
logging.getLogger('autogen.import_utils').setLevel(logging.INFO)
# Also silence the httpcore logs which are quite verbose
logging.getLogger('httpcore').setLevel(logging.INFO)
# And suppress the asyncio errors about tasks being destroyed
logging.getLogger('asyncio').setLevel(logging.ERROR)
