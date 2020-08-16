from recurrent.event_parser import RecurringEvent

def parse(s, now=None):
    return RecurringEvent(now).parse(s)

def deparse(r, now=None):
    return RecurringEvent(now).deparse(r)
