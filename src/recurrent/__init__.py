import logging

log = logging.getLogger(__name__)
try:
    # Prevent output if no handler set
    log.addHandler(logging.NullHandler())
except AttributeError:
    pass

from event_parser import RecurringEvent

def parse(s, now=None):
    return RecurringEvent(now).parse(s)
