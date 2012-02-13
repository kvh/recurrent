import re
import datetime
import logging
import parsedatetime
pdt = parsedatetime.Calendar()

from constants import *

log = logging.getLogger('recurrent')
log.setLevel(logging.CRITICAL)

RE_START = r'(start(?:s|ing)?)\s(?P<starting>.*)'
RE_EVENT = r'(?P<event>(?:every|each|\bon\b|repeat|%s|%s)(?:s|ing)?(.*))'%(
        RE_DAILY.pattern, RE_PLURAL_WEEKDAY.pattern)
RE_END = r'(?:\bend|until)(?:s|ing)?(?P<ending>.*)'
RE_START_EVENT = re.compile(r'^%s\s%s' % (RE_START, RE_EVENT))
RE_EVENT_START = re.compile(r'^%s\s%s' % (RE_EVENT, RE_START))
RE_FROM_TO = re.compile(r'^(?P<event>.*)from(?P<starting>.*)(to|through|thru)(?P<ending>.*)')
RE_START_END = re.compile(r'^%s\s%s' % (RE_START, RE_END))
RE_OTHER_END = re.compile(r'^(?P<other>.*)\s%s' % RE_END)


def normalize(s):
    s = s.strip().lower()
    s = re.sub('\W&\S', '', s)
    return re.sub('\s+', ' ', s)


class Token(object):
    def __init__(self, text, all_text, type_):
        self.text = text
        self.all_text = all_text
        self.type_ = type_

    def __repr__(self):
        return '<Token %s: %s>' % (self.text, self.type_)


class Tokenizer(list):
    TYPES = (
            ('daily', RE_DAILY),
            ('every', RE_EVERY),
            ('through', RE_THROUGH),
            ('unit', RE_UNITS),
            ('recurring_unit', RE_RECURRING_UNIT),
            ('ordinal', RE_ORDINAL),
            ('number', RE_NUMBER),
            ('plural_weekday', RE_PLURAL_WEEKDAY),
            ('DoW', RE_DOW),
            ('MoY', RE_MOY),
        )

    def __init__(self, text):
        super(Tokenizer, self).__init__(self)
        self.text = text
        s = self.text
        self._index = 0
        for token in s.split():
            for type_, regex in self.TYPES:
                m = regex.match(token)
                if m:
                    self.append(Token(token, s, type_))
                    break
        log.debug("tokenized '%s'\n%s" %(self.text, self))

    @property
    def types(self):
        return [t.type_ for t in self]

    def types_set(self):
        return set(self.types)


class RecurringEvent(object):
    def __init__(self, now_date=None):
        if now_date is None:
            now_date = datetime.datetime.now()
        self.now_date = now_date

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
        for k, v in params.items():
            if isinstance(v, str) or isinstance(v, int):
                if isinstance(v, str):
                    v = v.upper()
                rules.append( '%s=%s' % (k.upper(), v))
        return rrule + ';'.join(rules)

    def parse(self, s):
        if not s:
            return False
        s = normalize(s)
        event = self.parse_start_and_end(s)
        if not event:
            return False
        return self.parse_event(event)

    def parse_start_and_end(self, s):
        m = RE_START_EVENT.match(s)
        if m:
            event = self.extract_ending(m.group('event'))
            self.dtstart = self.parse_date(m.group('starting'))
            return event
        m = RE_EVENT_START.match(s)
        if m:
            event = m.group('event')
            start = self.extract_ending(m.group('starting'))
            self.dtstart = self.parse_date(start)
            return event
        m = RE_FROM_TO.match(s)
        if m:
            event = m.group('event')
            self.dtstart = self.parse_date(m.group('starting'))
            self.until = self.parse_date(m.group('ending'))
            return event

        return self.extract_ending(s)

    def extract_ending(self, s):
        m = RE_OTHER_END.match(s)
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

    def parse_event(self, s):
        tokens = Tokenizer(s)

        # daily
        if 'daily' in tokens.types_set():
            self.interval = 1
            self.freq = 'daily'
            return True

        # explicit weekdays
        if 'plural_weekday' in tokens.types_set():
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
        if 'every' in tokens.types_set() or 'recurring_unit' in tokens.types_set():
            if 'every other' in s:
                self.interval = 2
            else:
                self.interval = 1
            if 'every' in tokens.types_set():
                i = tokens.types.index('every')
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
                    while index + 1 < len(tokens) and tokens.types[index + 1] == 'ordinal':
                        ords.append(get_ordinal_index(tokens[index + 1].text))
                        index += 1

                    if index + 1 < len(tokens) and tokens.types[index + 1] == 'DoW':
                        # "first wednesday of/in ..."
                        dow = get_DoW(tokens[index + 1].text)
                        self.ordinal_weekdays.extend( ['%s%s' % (i, dow) for i in ords] )
                        index += 1
                        if index >= len(tokens): break
                    elif index + 1 < len(tokens) and tokens.types[index + 1] == 'unit':
                        # "first of the month/year"
                        self.freq = get_unit_freq(tokens[index + 1].text)
                        if self.freq == 'monthly':
                            self.bymonthday.extend([str(i) for i in ords])
                        if self.freq == 'yearly':
                            self.byyearday.extend([str(i) for i in ords])
                        index += 1
                        if index >= len(tokens): break
                elif tokens.types[index] == 'DoW':
                    if not self.freq:
                        self.freq = 'weekly'
                    self.weekdays.append(get_DoW(tokens[index].text))
                elif tokens.types[index] == 'MoY':
                    if not self.freq:
                        self.freq = 'yearly'
                    self.bymonth.append(str(get_MoY(tokens[index].text)))
                    #TODO: should iterate this ordinal as well...
                    if index + 1 < len(tokens) and tokens[index + 1].type_ == 'ordinal':
                        self.ordinal_weekdays.append(str(get_ordinal_index(tokens[index
                            + 1].text)))
                index += 1
            return True
        # No recurring match, return false
        return False

if __name__ == '__main__':
    r = RecurringEvent(datetime.datetime(2010, 1, 1))
    print r.parse_date('march 3rd')
    r.parse('daily starting march 3rd')
    print r.get_RFC_rrule()

