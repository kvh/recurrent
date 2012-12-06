from event_parser import RecurringEvent

def parse(s, now=None):
    return RecurringEvent(now).parse(s)
