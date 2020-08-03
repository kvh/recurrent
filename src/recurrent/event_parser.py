import re
import datetime
import logging
import sys

try:
    from parsedatetime import parsedatetime
except ImportError:
    import parsedatetime

pdt = parsedatetime.Calendar()

from recurrent.constants import *

DEBUG=False

log = logging.getLogger('recurrent')
if DEBUG:
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler(sys.stderr))
else:
    log.addHandler(logging.NullHandler())   # Issue #4

# Issue #14 RE_TIME = re.compile(r'(?P<hour>\d{1,2}):?(?P<minute>\d{2})?\s?(?P<mod>am|pm)?(oclock)?')
RE_TIME = re.compile(r'(?P<hour>\d{1,2}):?(?P<minute>\d{2})?\s?(?P<mod>am?|pm?)?(oclock)?')
RE_DEF_TIME = re.compile(r'[:apo]')             # Issue #13: Time with a ':', 'am', 'pm', or 'oclock'
RE_AT_TIME = re.compile(r'at\s%s' % RE_TIME.pattern)
RE_AT_TIME_END = re.compile(r'at\s%s$' % RE_TIME.pattern)
RE_STARTING = re.compile(r'start(?:s|ing)?')
RE_ENDING = re.compile(r'(?:\bend|until)(?:s|ing)?')
RE_REPEAT = re.compile(r'(?:every|each|\bon\b|repeat(s|ing)?)')
RE_START = r'(%s)\s(?P<starting>.*)' % RE_STARTING.pattern
RE_EVENT = r'(?P<event>(?:every|each|\bon\b|repeat|%s|%s)(?:s|ing)?(.*))'%(
        RE_DAILY.pattern, RE_PLURAL_WEEKDAY.pattern)
RE_END = r'%s(?P<ending>.*)' % RE_ENDING.pattern
RE_START_EVENT = re.compile(r'%s\s%s' % (RE_START, RE_EVENT))
RE_EVENT_START = re.compile(r'%s\s%s' % (RE_EVENT, RE_START))
RE_FROM_TO = re.compile(r'(?P<event>.*)from(?P<starting>.*)(to|through|thru)(?P<ending>.*)')
RE_START_END = re.compile(r'%s\s%s' % (RE_START, RE_END))
RE_OTHER_END = re.compile(r'(?P<other>.*)\s%s' % RE_END)
RE_SEP = re.compile(r'(from|to|through|thru|on|at|of|in|a|an|the|and|or|both)$')
RE_AMBIGMOD = re.compile(r'(this|next|last)$')
RE_OTHER = re.compile(r'other|alternate')
RE_AMPM = re.compile(r'am?|pm?|oclock')     # Issue #13


def normalize(s):
    s = s.strip().lower()
    s = re.sub(r'\W&\S', '', s)
    return re.sub(r'\s+', ' ', s)


class Token(object):
    def __init__(self, text, all_text, type_):
        self.text = text
        self.all_text = all_text
        self.type_ = type_

    def __repr__(self):
        return '<Token %s: %s>' % (self.text, self.type_)


class Tokenizer(list):
    CONTENT_TYPES = (
            ('daily', RE_DAILY),
            ('every', RE_EVERY),
            ('through', RE_THROUGH),
            # Issue #16 ('unit', RE_UNITS),
            ('recurring_unit', RE_RECURRING_UNIT),
            ('ordinal', RE_ORDINAL),
            ('unit', RE_UNITS), # Issue #16: classify 'second' as ordinal
            ('number', RE_NUMBER),
            ('plural_weekday', RE_PLURAL_WEEKDAY),
            ('DoW', RE_DOW),
            ('MoY', RE_MOY)
            )
    TYPES = CONTENT_TYPES + (
            ('ambigmod', RE_AMBIGMOD),
            ('starting', RE_STARTING),
            ('ending', RE_ENDING),
            ('repeat', RE_REPEAT),
            ('sep', RE_SEP),
            ('time', RE_TIME),
            ('other', RE_OTHER),
            ('ampm', RE_AMPM),      # Issue #13
        )

    def __init__(self, text):
        super(Tokenizer, self).__init__(self)
        self.text = text
        s = self.text
        self._index = 0
        self.all_ = []
        for token in s.split():
            for type_, regex in self.TYPES:
                m = regex.match(token)
                if m:
                    tok = Token(token, s, type_)
                    self.append(tok)
                    self.all_.append(tok)
                    break
            else:
                self.all_.append(Token(token, s, None))
        log.debug("tokenized '%s'\n%s" %(self.text, self))

    def largest_contiguous_substring(self):
        ls = 0
        s = 0
        l = 0
        for i, t in enumerate(self.all_ + [Token('', '', None)]):
            if t.type_ == None:
                if i - s > l:
                    # accept only if some non-filler tokens exist
                    if sum([t.type_ in ('sep', 'starting', 'ending', 'ambigmod', 'repeat') for t in self.all_[s:i]]
                            ) < i - s:
                        l = i - s
                        ls = s
                s = i + 1
        return self.all_[ls:ls+l]

    @property
    def types(self):
        return [t.type_ for t in self]

    def types_set(self):
        return set(self.types)


class RecurringEvent(object):
    def __init__(self, now_date=None, preferred_time_range=(8, 19)):
        if now_date is None:
            now_date = datetime.datetime.now()
        self.now_date = now_date
        self.preferred_time_range = preferred_time_range
        self._reset()

    def _reset(self):
        # rrule params
        self.dtstart = None
        self.until = None
        self.interval = None
        self.freq = None
        self.weekdays = []
        self.ordinal_weekdays = []
        self.byday = None
        self.bymonthday = []
        self.byyearday = []
        self.bymonth = []
        self.byhour = []
        self.byminute = []

        # not supported currently
        self.count = None
        self.bysetpos = None
        self.byweekno = None

    def get_params(self):
        params = {}
        # we shouldnt have weekdays and ordinal weekdays but if we do ordinal weekdays
        # take precedence.
        if not self.ordinal_weekdays and self.weekdays:
            params['byday'] =','.join(self.weekdays)
        elif self.ordinal_weekdays:
            params['byday'] = ','.join(self.ordinal_weekdays)

        if self.bymonthday:
            params['bymonthday'] = ','.join(self.bymonthday)
        if self.byyearday:
            params['byyearday'] = ','.join(self.byyearday)
        if self.bymonth:
            params['bymonth'] = ','.join(self.bymonth)
        if self.byhour:
            params['byhour'] = ','.join(self.byhour)
        if self.byminute:
            params['byminute'] = ','.join(self.byminute)
        if self.interval is not None:
            params['interval'] = self.interval
        if self.freq is not None:
            params['freq'] = self.freq
        if self.dtstart:
            params['dtstart'] = self.dtstart.strftime('%Y%m%d')
        if self.until:
            params['until'] = self.until.strftime('%Y%m%d')
        return params

    def get_RFC_rrule(self):
        rrule = ''
        params = self.get_params()
        if 'dtstart' in params:
            rrule += 'DTSTART:%s\n' % params.pop('dtstart')
        rrule += "RRULE:"
        rules = []
        for k, v in list(params.items()):
            if isinstance(v, str) or isinstance(v, int):
                if isinstance(v, str):
                    v = v.upper()
                rules.append( '%s=%s' % (k.upper(), v))
        return rrule + ';'.join(rules)

    def parse(self, s):
        # returns a rrule string if it is a recurring date, a datetime.datetime
        # if it is a non-recurring date, and none if it is neither.
        self._reset()
        if not s:
            return False
        s = normalize(s)
        #self.tokens = Tokenizer(s)
        #toks = self.tokens.largest_contiguous_substring()
        #s = ' '.join([t.text for t in toks])
        #log.debug("Event substring: %s" % s)
        event = self.parse_start_and_end(s)
        if not event:
            return False
        self.is_recurring = self.parse_event(event)
        if self.is_recurring:
            # get time if its obvious
            m = RE_AT_TIME.search(s)
            if not m:                       # Issue #13
                m = RE_TIME.match(s)        # Issue #13
                if m and not RE_DEF_TIME.search(m.group(0)):    # Issue #13: We have to be sure this is a time
                    m = None                # Issue #13
            if m:
                self.byhour.append(str(self.get_hour(m.group('hour'), m.group('mod'))))
                mn = m.group('minute')
                if mn is None:
                    mn = 0
                try:
                    mn = int(mn)
                    self.byminute.append(str(mn))
                except ValueError:
                    pass
            return self.get_RFC_rrule()
        date = self.parse_date(s)
        if date is not None:
            date, found = self.parse_time(s, date)
            return date
        # maybe we have a simple time expression
        date, found = self.parse_time(s, self.now_date)
        if found:
            return date
        return None

    def parse_time(self, s, dt):
        m = RE_AT_TIME.search(s)
        if not m:                       # Issue #13
            m = RE_TIME.match(s)        # Issue #13: Ok not to have 'at' if the string starts with a definite time
            if m and not RE_DEF_TIME.search(m.group(0)):    # Issue #13: We have to be sure this is a time
                m = None                # Issue #13
        if m:
            hr = self.get_hour(m.group('hour'), m.group('mod'))
            mn = m.group('minute')
            try:
                mn = int(mn)
            except (TypeError, ValueError):
                mn = None
            try:
                hr = int(hr)
            except (TypeError, ValueError):
                hr = None
            if hr is not None:
                if mn is not None:
                    return dt.replace(hour=hr, minute=mn), True
                return dt.replace(hour=hr), True
        return dt, False

    def parse_start_and_end(self, s):
        m = RE_START_EVENT.search(s)
        if m:
            event = self.extract_ending(m.group('event'))
            self.dtstart = self.parse_date(m.group('starting'))
            return event
        m = RE_EVENT_START.search(s)
        if m:
            event = m.group('event')
            start = self.extract_ending(m.group('starting'))
            self.dtstart = self.parse_date(start)
            return event
        m = RE_FROM_TO.search(s)
        if m:
            event = m.group('event')
            self.dtstart = self.parse_date(m.group('starting'))
            self.until = self.parse_date(m.group('ending'))
            return event

        return self.extract_ending(s)

    def extract_ending(self, s):
        m = RE_OTHER_END.search(s)
        if m:
            self.until = self.parse_date(m.group('ending'))
            return m.group('other')
        return s

    def parse_date(self, date_string):
        timestruct, result = pdt.parse(date_string, self.now_date)
        if result:
            log.debug( "parsed date string '%s' to %s" %(date_string,
                    timestruct[:6]))
            return datetime.datetime(*timestruct[:6])
        return None

    def eat_times(self, tokens):              # Issue #13
        # Handle things like "at 10" or "10 am" and eat the 'number' token since we handle it elsewhere
        for i in range(len(tokens)):
            if tokens[i].type_ == 'number' and \
              ((i+1 < len(tokens) and tokens[i+1].type_ == 'ampm') or \
               (i != 0 and tokens[i-1].type_ == 'sep' and tokens[i-1].text == 'at')):
                #log.debug(f'eat_times: del {tokens[i]}')
                del tokens[i]
                break
        return tokens

    def parse_event(self, s):
        tokens = Tokenizer(s)
        tokens = self.eat_times(tokens)      # Issue #13
        tokens = [t for t in tokens if t.type_ in [x[0] for x in Tokenizer.CONTENT_TYPES] ]
        if not tokens:
            return False
        types = set([t.type_ for t in tokens])

        # daily
        if 'daily' in types:
            self.interval = 1
            self.freq = 'daily'
            return True

        # explicit weekdays
        if 'plural_weekday' in types:
            if 'weekdays' in s:
                # "RRULE:FREQ=WEEKLY;WKST=MO;BYDAY=MO,TU,WE,TH,FR"
                self.interval = 1
                self.freq = 'weekly'
                self.weekdays = ['MO','TU','WE','TH','FR']
            elif 'weekends' in s:
                self.interval = 1
                self.freq = 'weekly'
                self.weekdays = ['SA','SU']
            else:
                # a plural weekday can really only mean one
                # of two things, weekly or biweekly
                self.freq = 'weekly'
                if 'bi' in s or 'every other' in s:
                    self.interval = 2
                else:
                    self.interval = 1
                for i, dow in enumerate(RE_DOWS):
                    if dow.search(s):
                        #this supports "thursdays and fridays"
                        self.weekdays.append(weekday_codes[i])
            return True

        # recurring phrases
        if 'every' in types or 'recurring_unit' in types:
            if 'every other' in s:
                self.interval = 2
            else:
                self.interval = 1
            if 'every' in types:
                i = ([t.type_ for t in tokens]).index('every')
                del tokens[i]

            index = 0
            while index < len(tokens):
                if tokens[index].type_ == 'number':
                    # we assume a bare number always specifies the interval
                    n = get_number(tokens[index].text)
                    if n is not None:
                        self.interval = n
                elif tokens[index].type_ == 'unit':
                    # we assume a bare unit (grow up...) always specifies the frequency
                    self.freq = get_unit_freq(tokens[index].text)
                elif tokens[index].type_ == 'ordinal':
                    ords = [get_ordinal_index(tokens[index].text)]

                    # grab all iterated ordinals (e.g. 1st, 3rd and 4th of
                    # november)
                    while index + 1 < len(tokens) and tokens[index + 1].type_ == 'ordinal':
                        ords.append(get_ordinal_index(tokens[index + 1].text))
                        index += 1

                    if ords[-1] == -1 and len(ords) != 1:       # Issue #18: 2nd to the last
                        ords = ords[:-1]                        # Issue #18
                        for i in range(len(ords)):              # Issue #18
                            ords[i] = -ords[i]                  # Issue #18

                    if index + 2 < len(tokens) and tokens[index + 1].type_ == 'unit' and \
                            tokens[index + 1].text == 'day' and tokens[index + 2].type_ == 'unit':  # Issue #18
                        index += 1      # Issue #18: Handle "first day of month" or "last day of month"

                    if index + 1 < len(tokens) and tokens[index + 1].type_ == 'DoW':
                        # "first wednesday of/in ..."
                        dow = get_DoW(tokens[index + 1].text)[0]
                        self.ordinal_weekdays.extend( ['%s%s' % (i, dow) for i in ords] )
                        index += 1
                        if index >= len(tokens): break
                    elif index + 1 < len(tokens) and tokens[index + 1].type_ == 'unit':
                        # "first of the month/year"
                        self.freq = get_unit_freq(tokens[index + 1].text)
                        if self.freq == 'monthly':
                            self.bymonthday.extend([str(i) for i in ords])
                        if self.freq == 'yearly':
                            self.byyearday.extend([str(i) for i in ords])
                        index += 1
                        if index >= len(tokens): break
                    elif len(ords) == 1 and ords[0] == 2:   # Issue #16: 'second' is ambiguous - treat here as unit
                        self.freq = 'secondly'              # Issue #16
                elif tokens[index].type_ == 'DoW':
                    # if we have a day of week, we can assume the frequency is
                    # weekly if it hasnt been set yet.
                    if not self.freq:
                        self.freq = 'weekly'
                    self.weekdays.extend(get_DoW(tokens[index].text))
                elif tokens[index].type_ == 'MoY':
                    # if we have a month we assume frequency is yearly
                    # if it hasnt been set.
                    if not self.freq:
                        self.freq = 'yearly'
                    self.bymonth.append(str(get_MoY(tokens[index].text)))
                    #TODO: should iterate this ordinal as well...
                    if index + 1 < len(tokens) and tokens[index + 1].type_ == 'ordinal':    # Aug 1st
                        self.bymonthday.append(str(get_ordinal_index(tokens[index
                            + 1].text)))
                    elif index + 1 < len(tokens) and tokens[index + 1].type_ == 'number':   # Issue #15: Aug 30
                        index += 1
                        n = get_number(tokens[index].text)
                        if n is not None:
                            self.bymonthday.append(str(n))
                index += 1
            return True
        # No recurring match, return false
        return False

    def get_hour(self, hr, mod):
        hr = int(hr)
        if mod is not None:
            # Issue #14 if mod == 'pm':
            if mod.startswith('p'): # Issue #14
                if hr == 12:        # Issue #14
                    return 12       # Issue #14
                return hr + 12
            if hr == 12:
                return 0
            return hr
        if hr > 12: return hr
        if hr < self.preferred_time_range[0]:
            return hr + 12
        return hr
