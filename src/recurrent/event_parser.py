import re
import datetime
import logging
import sys
import calendar
#import traceback

try:
    from parsedatetime import parsedatetime
except ImportError:     # pragma nocover
    import parsedatetime

from recurrent.constants import *

DEBUG=False

log = logging.getLogger('recurrent')
if DEBUG:               # pragma nocover
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler(sys.stderr))
else:
    log.addHandler(logging.NullHandler())   # Issue #4

# Issue #14 RE_TIME = re.compile(r'(?P<hour>\d{1,2}):?(?P<minute>\d{2})?\s?(?P<mod>am|pm)?(oclock)?')
RE_TIME = re.compile(r'(?P<hour>\d{1,2}):?(?P<minute>\d{2})?\s?(?P<mod>am?|pm?)?(o\'?clock)?')
RE_DEF_TIME = re.compile(r'[:apo]')             # Issue #13: Time with a ':', 'am', 'pm', or 'oclock'
RE_AT_TIME = re.compile(r'at\s%s' % RE_TIME.pattern)
RE_AT_TIME_END = re.compile(r'at\s%s$' % RE_TIME.pattern)
RE_STARTING = re.compile(r'start(?:s|ing)?')
RE_ENDING = re.compile(r'(?:\bend|until)(?:s|ing)?')
RE_REPEAT = re.compile(r'(?:every|each|\bon\b|repeat(s|ing)?)')
RE_START = r'(%s)\s(?P<starting>.*)' % RE_STARTING.pattern
RE_START_SHORT = r'(%s)\s(?P<starting>.*?)' % RE_STARTING.pattern
RE_EVENT = r'(?P<event>(?:every|each|\bon\b|\bthe\b|repeat|%s|%s|%s)(?:s|ing)?(.*))'%(
        RE_DAILY.pattern, RE_PLURAL_WEEKDAY.pattern, RE_ORDINAL_NOT_ANCHORED.pattern)
RE_EVENT_NO_ORD = r'(?P<event>(?:every|each|\bon\b|\bthe\b|repeat|%s|%s)(?:s|ing)?(.*))'%(
        RE_DAILY.pattern, RE_PLURAL_WEEKDAY.pattern)
RE_END = r'%s(?P<ending>.*)' % RE_ENDING.pattern
RE_START_EVENT = re.compile(r'%s\s%s' % (RE_START_SHORT, RE_EVENT_NO_ORD))
RE_EVENT_START = re.compile(r'%s\s%s' % (RE_EVENT, RE_START))
RE_FROM_TO = re.compile(r'(?P<event>.*)from(?P<starting>.*)(to|through|thru|until)(?P<ending>.*)')
RE_COUNT = re.compile(r'(?P<event>.*?)(?:\bfor\s+|\b(?:for\s+)?up\s+to\s+)?(?:(?P<twice>twice)|(?P<count>%s)(?:x|\s*times|\s*occurrences))'%RE_NUMBER_NOT_ANCHORED.pattern)
RE_COUNT_UNTIL1 = re.compile(r'(?P<event>.*?)(?:\bfor\s+the\s+next\s+|\bfor\s+(?:up\s+to\s+)?)\s*(?P<unit>week|month|year)')
RE_COUNT_UNTIL = re.compile(r'(?P<event>.*?)(?:\bfor\s+the\s+next\s+|\bfor\s+(?:up\s+to\s+)?)(?P<count>%s)\s*(?P<unit>weeks|months|years)'%RE_NUMBER_NOT_ANCHORED.pattern)
RE_START_END = re.compile(r'%s\s%s' % (RE_START, RE_END))
RE_OTHER_END = re.compile(r'(?P<other>.*)\s%s' % RE_END)
RE_SEP = re.compile(r'(from|to|through|thru|on|at|of|in|a|an|the|and|or|both)$')
RE_AMBIGMOD = re.compile(r'(this|next|last)$')
RE_OTHER = re.compile(r'other|alternate')
RE_AMPM = re.compile(r'am?|pm?|o\'?clock')     # Issue #13
RE_LONG_DATE_START = re.compile(r'(%s),\s*(%s)' % (RE_DOW, RE_MOY_NOT_ANCHORED))
RE_EXCEPT = re.compile(r'(?P<event>.*?)\bexcept(?:\s+for\s|\s+on\s+|\s+in\s+)?(?P<except>.*)$')
RE_YEAR = re.compile(r'\b(\d\d\d\d)\b')
RE_ORD_DAY_WEEK_MONTH_OR_YEAR = re.compile(r'(?P<ord>%s)\s+(?P<unit>(?:%s|day|week|month|year)\b)'%(RE_ORDINAL_NOT_ANCHORED.pattern, RE_DOW.pattern))
RE_THRU = re.compile(r'(?P<first>%s|%s)(?:[-]|\s+thru\s+|\s+through\s+)(?P<second>%s|%s)'%(RE_PLURAL_DOW.pattern, RE_DOW.pattern, RE_PLURAL_DOW.pattern, RE_DOW.pattern))
RE_BEGIN_END_OF = re.compile(r'(?P<be>beginning|begin|start|ending|end)\s+of\b')                      # Issue #12
RE_AT_BEGIN_END = re.compile(r'\bat(\s+the)?\s+(?P<be>beginning\b|begin\b|start\b|ending\b|end\b)')     # Issue #12
RE_RRULE = re.compile(r'^RRULE:(?P<rr>.*)$', re.M)
RE_BYSETPOS = re.compile(r'\binstance\b|\boccurrence\b')

def normalize(s):
    s = s.strip().lower()
    s = re.sub(r',\s*(\d\d\d\d)', r' \1', s) # Remove commas in dates before the year
    s = re.sub(RE_LONG_DATE_START, r'\1 \2', s) # Remove commas in long format dates, e.g. "Tuesday, January..."
    s = re.sub(r',\s*and', ' and', s)       # Remove commas before 'and'
    s = re.sub(r',', ' and ', s)            # Change all other commas to ' and '
    s = re.sub(r'[^\w\s\./:-]', '', s)      # Allow . for international formatting
    s = re.sub(r'\s+', ' ', s)
    return s

def handle_begin_end(s):                # Issue #12
    def sub_be1(m):
        if m.group('be').startswith('e'):
            return 'last of'
        else:
            return 'first of'
    def sub_be2(m):
        if m.group('be').startswith('e'):
            return 'on the last'
        else:
            return 'on the first'
    s = re.sub(RE_BEGIN_END_OF, sub_be1, s)
    s = re.sub(RE_AT_BEGIN_END, sub_be2, s)
    return s

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
            ('MoY', RE_MOY),
            ('instances', RE_BYSETPOS)
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

class RecurringEvent(object):
    def __init__(self, now_date=None, preferred_time_range=(8, 19), parse_constants: parsedatetime.Constants=None):
        if now_date is None:
            now_date = datetime.datetime.now()
        if isinstance(now_date, datetime.date) and not isinstance(now_date, datetime.datetime):
            now_date = datetime.datetime(now_date.year, now_date.month, now_date.day)
        self.now_date = now_date
        self.preferred_time_range = preferred_time_range
        self.pdt = parsedatetime.Calendar(constants=parse_constants)
        self._reset()
        
        if parse_constants and parse_constants.use24:
            # the 24hr clock will always have this preferred time
            # will not break pm specification
            preferred_time_range = (0,12)

    def _reset(self):
        # rrule params
        self.dtstart = None
        self.until = None
        self.count = None
        self.exdate = None
        self.exrule = None
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
        self.bysetpos = []
        self.byweekno = []

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
        if self.bysetpos:
            params['bysetpos'] = ','.join(self.bysetpos)
        if self.byweekno:
            params['byweekno'] = ','.join(self.byweekno)
        if self.interval is not None:
            params['interval'] = self.interval
        if self.freq is not None:
            params['freq'] = self.freq
        if self.dtstart:
            params['dtstart'] = self.dtstart.strftime('%Y%m%d')
        if self.until:
            params['until'] = self.until.strftime('%Y%m%d')
        elif self.count:
            params['count'] = self.count
        if self.exrule:
            params['exrule'] = self.exrule
        if self.exdate:
            params['exdate'] = self.exdate
        return params

    def get_RFC_rrule(self):
        rrule = ''
        params = self.get_params()
        if 'freq' not in params:
            return None                     # Not a valid RRULE
        if 'dtstart' in params:
            rrule += 'DTSTART:%s\n' % params.pop('dtstart')
        exdate = params.pop('exdate', None)
        exrule = params.pop('exrule', None)
        rrule += "RRULE:"
        rules = []
        for k, v in list(params.items()):
            if isinstance(v, str) or isinstance(v, int):
                if isinstance(v, str):
                    v = v.upper()
                rules.append( '%s=%s' % (k.upper(), v))
        result = rrule + ';'.join(rules)
        if exrule is not None:
            result += '\nEXRULE:' + exrule
        if exdate is not None:
            exd = ','.join(self.adjust_exdates(result, exdate))
            if exd:
                exdate = '\nEXDATE:' + exd
                result += exdate
        return result

    def parse(self, s):
        # returns a rrule string if it is a recurring date, a datetime.datetime
        # if it is a non-recurring date, and None if it is neither.
        self._reset()
        if not s:
            return None
        s = normalize(s)
        s = handle_begin_end(s)         # Issue #12
        event = self.parse_start_and_end(s)
        if not event:
            return None
        self.is_recurring = self.parse_event(event)
        if self.is_recurring:
            # get time if its obvious
            m = RE_AT_TIME.search(event)
            if not m:                       # Issue #13
                m = RE_TIME.match(event)        # Issue #13
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
                except ValueError:      # pragma nocover
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
            except (TypeError, ValueError):     # pragma nocover
                hr = None
            try:
                if hr is not None:
                    if mn is not None:
                        return dt.replace(hour=hr, minute=mn), True
                    return dt.replace(hour=hr), True
            except ValueError:
                pass
        return dt, False

    @staticmethod
    def increment_date(d, amount, units='years'):
        """Return a date that's `amount` years, months, weeks, or days after the date (or datetime)
        object `d`. Return the same calendar date (month and day) in the
        destination, if it exists, otherwise use the following day
        (thus changing February 29 to March 1).

        """
        if units == 'years':
            try:
                return d.replace(year = d.year + amount)
            except ValueError:
                return d + (datetime.date(d.year + amount, 1, 1) - datetime.date(d.year, 1, 1))
        elif units == 'months':
            years = 0
            month = d.month + amount
            if month > 12:
                years, month = divmod(month-1, 12)
                month += 1
            try:
                return d.replace(year = d.year + years, month=month)
            except ValueError:
                return d + (datetime.date(d.year + years, month, 1) - datetime.date(d.year, month, 1))
        else:
            multiplier = 1
            if units == 'weeks':
                multiplier = 7
            return d + datetime.timedelta(days=amount*multiplier)

    def parse_start_and_end(self, s):
        m = RE_EXCEPT.match(s)
        if m:
            s = m.group('event')
            exc = m.group('except')
            # Handle either a recurrence or a list of dates or months
            r = RecurringEvent(now_date=self.now_date, preferred_time_range=self.preferred_time_range)
            rfc = r.parse(exc)
            if isinstance(rfc, str):
                self.exrule = RE_RRULE.search(rfc).group('rr')
            else:
                self.exdate = self.extract_exdates(m.group('except'))
        m = RE_START_EVENT.search(s)
        if m:
            self.dtstart = self.parse_date(m.group('starting'))
            event = self.extract_ending(m.group('event'))
            return event
        m = RE_EVENT_START.search(s)
        if m:
            event = m.group('event')
            start = self.extract_ending(m.group('starting'))
            self.dtstart = self.parse_date(start)
            if self.until and self.until < self.dtstart:       # e.g. from Nov to Jun
                self.until = self.increment_date(self.until, 1)
            return event
        m = RE_FROM_TO.search(s)
        if m:
            event = m.group('event')
            self.dtstart = self.parse_date(m.group('starting'))
            self.until = self.parse_date(m.group('ending'))
            if self.until < self.dtstart:       # e.g. from Nov to Jun
                self.until = self.increment_date(self.until, 1)
            return event

        return self.extract_ending(s)

    def extract_ending(self, s):
        m = RE_OTHER_END.search(s)
        if m:
            self.until = self.parse_date(m.group('ending'))
            if self.dtstart and self.until < self.dtstart:       # e.g. starting Nov until Jun
                self.until = self.increment_date(self.until, 1)
            return m.group('other')
        m = RE_COUNT.search(s)
        if m:
            event = m.group('event')
            twice = m.group('twice')
            count = m.group('count')
            if twice:
                count = 2
            self.count = get_number(count)
            return event
        m = RE_COUNT_UNTIL1.search(s)
        if m:
            event = m.group('event')
            unit = m.group('unit')
            self.until = self.increment_date(self.now_date, 1, unit + 's')
            return event
        m = RE_COUNT_UNTIL.search(s)
        if m:
            event = m.group('event')
            count = m.group('count')
            unit = m.group('unit')
            self.until = self.increment_date(self.now_date, get_number(count), unit)
            return event
        return s

    def extract_exdates(self, s):
        """Walk thru the "except on" dates and create a list of them, noting which ones have no times specified"""
        result = []
        s_split = s.split(' and ')
        for d_str in s_split:
            m = RE_MOY_NOT_ANCHORED.match(d_str)    # Month
            if m:
                rest = d_str[len(m.group(0)):].strip()
                yr = None
                y = RE_YEAR.match(rest)
                if not rest or y or not rest[0].isdigit():  # e.g. may; may 2020; may would work, but not may 1
                    if y:
                        yr = int(y.group(1))              # e.g. Feb 2020
                    dt = [get_MoY(m.group(0)), yr]
                    result.append(dt)
                    continue

            dt = self.parse_date(d_str)
            if dt:
                matches = RE_TIME.finditer(d_str)
                for m in matches:
                    if RE_DEF_TIME.search(m.group(0)):
                        break
                else:
                    dt = dt.date()      # Didn't find any definite times

                result.append(dt)
        log.debug(f'extract_exdates({s}) = {result}')
        return result

    def adjust_exdates(self, rrules, exdate):
        """Adjust a list of exdates to ensure they specify the times and then properly format them for the EXDATE rule, so
        things like "daily at 2pm except for tomorrow" will work properly"""
        def date_key(ex):
            if isinstance(ex, datetime.datetime):
                return ex
            elif isinstance(ex, list):
                if ex[1] is not None:
                    return datetime.datetime(ex[1], ex[0], 1)
                elif (self.dtstart and ex[0] < self.dtstart.month) or ex[0] < self.now_date.month:
                    return datetime.datetime(self.now_date.year+1, ex[0], 1)
                else:
                    return datetime.datetime(self.now_date.year, ex[0], 1)
            else:       # date
                return datetime.datetime(ex.year, ex.month, ex.day)

        exdate.sort(key=date_key)
        needs_time = False
        for ex in exdate:
            if not isinstance(ex, datetime.datetime):
                needs_time = True
                break
        if needs_time:
            new_exdate = []
            try:
                from dateutil.rrule import rrulestr
                rs = rrulestr(rrules, dtstart=self.now_date)
                ndx = 0
                for r in rs:
                    while True:
                        ex = exdate[ndx]
                        if isinstance(ex, datetime.datetime):
                            if r == ex:
                                new_exdate.append(ex)
                            if r >= ex:
                                ndx += 1
                                if ndx >= len(exdate):
                                    break
                                continue    # pragma nocover (see https://github.com/nedbat/coveragepy/issues/198)
                            break
                        elif isinstance(ex, list): # A month, with an optional year
                            if r.month == ex[0] and (ex[1] is None or r.year == ex[1]):
                                ex[1] = r.year          # Claim the year
                                new_exdate.append(r)
                            if ex[1] is not None and (r.year > ex[1] or (r.year == ex[1] and r.month > ex[0])):
                                ndx += 1
                                if ndx >= len(exdate):
                                    break
                                continue    # pragma nocover
                            break
                        else:       # A date
                            rd = r.date()
                            if rd == ex:
                                new_exdate.append(r)
                            if rd > ex:
                                ndx += 1
                                if ndx >= len(exdate):
                                    break
                                continue    # pragma nocover
                            break
                    if ndx >= len(exdate):
                        break
                exdate = new_exdate
            except Exception as e:      # pragma nocover
                log.debug(f'adjust_exdates({rrules}, {exdate}): Exception {e}')
        result = [e.strftime('%Y%m%dT%H%M%S') for e in exdate]
        log.debug(f'adjust_exdates({rrules}, {exdate}) = {result}')
        return result

    def parse_date(self, date_string):
        result = self.parse_singleton(date_string)
        if result:
            log.debug(f"parsed date string '{date_string}' to {result}")
            return result
        timestruct, result = self.pdt.parse(date_string, self.now_date)
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

    def fixup_ord_intervals(self, s):
        def ord_sub(m):         # Replace every 2nd day => every 2 days; every 3rd month => every 3 months; every 4th year => every 4 years; every 5th fri => every 5 fridays
            ordx = get_ordinal_index(m.group('ord'))
            unit = m.group('unit')
            if unit == 'day' and ('week' in s or 'month' in s or 'year' in s):   # e.g. last day of each month; every year on the 31st day
                return m.group(0)               # Don't change this kind!
            if unit == 'day' or unit == 'week' or unit == 'month' or unit == 'year':
                unit += 's'
            elif RE_MOY_NOT_ANCHORED.search(s) or 'week' in s or 'month' in s:     # e.g. fourth thu of march, third fri of each month
                return m.group(0)                                   # Don't change this kind!
            else:
                unit = ' and '.join([plural_day_names[u].lower() for u in get_DoW(unit)])
            return f'{ordx} {unit}'

        if not RE_REPEAT.search(s):
            return s
        return re.sub(RE_ORD_DAY_WEEK_MONTH_OR_YEAR, ord_sub, s)

    def process_thru(self, s):
        """Handle things like "Mon-Sat", "Fri thru Sun", "tuesdays through thursdays" """
        def sub_thru(m):
            first = m.group('first')
            second = m.group('second')
            dn = plural_day_names if first.endswith('s') or second.endswith('s') else day_names
            first = get_DoW(first)
            second = get_DoW(second)
            result = []
            if first == second:     # Mon-Mon
                result.extend(first)
            else:
                while True:
                    result.extend(first)
                    first = [next_day[first[-1]]]
                    if first[0] == second[0]:
                        result.extend(second)
                        break
            result = ' and '.join([dn[n].lower() for n in result])
            log.debug(f'process_thru({s}) = {result}')
            return result

        return re.sub(RE_THRU, sub_thru, s)

    def handle_Nth_to_the_last(self, tokens):       # Issue #18
        """Differentiate between 2nd and last vs. 2nd to the last or 2nd last. For
        the latter case, insert a '-' before the text of the prior ordinal to signify
        that it should be interpreted from the other end"""
        i = 0
        while i < len(tokens):
            if tokens[i].type_ == 'ordinal' and tokens[i].text == 'last':
                for j in range(i-1, -1, -1):
                    if tokens[j].type_ == 'sep':
                        if tokens[j].text == 'and':
                            break
                    elif tokens[j].type_ == 'ordinal':
                        tokens[j].text = '-' + tokens[j].text
                        del tokens[i]
                        i -= 1
            i += 1
        return tokens

    def parse_event(self, s):
        s = self.fixup_ord_intervals(s)
        s = self.process_thru(s)
        tokens = Tokenizer(s)
        tokens = self.handle_Nth_to_the_last(tokens)        # Issue #18
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
        if 'plural_weekday' in types and 'ordinal' not in types:
            def plural_weekday_interval():
                if 'bi' in s or 'every other' in s:
                    return 2
                elif 'number' in types:
                    i = ([t.type_ for t in tokens]).index('number')
                    n = get_number(tokens[i].text)
                    if n is not None:
                        return n
                return 1

            if 'weekdays' in s:
                # "RRULE:FREQ=WEEKLY;WKST=MO;BYDAY=MO,TU,WE,TH,FR"
                self.interval = plural_weekday_interval()
                self.freq = 'weekly'
                self.weekdays = ['MO','TU','WE','TH','FR']
            elif 'weekends' in s:
                self.interval = plural_weekday_interval()
                self.freq = 'weekly'
                self.weekdays = ['SA','SU']
            else:
                # a plural weekday can really only mean one
                # of two things, weekly or biweekly
                self.freq = 'weekly'
                self.interval = plural_weekday_interval()
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
                    text = tokens[index].text
                    if text == 'day' or text == 'week': # Day or week of month/year
                        got_some = False
                        while True:
                            if index + 1 < len(tokens) and tokens[index + 1].type_ == 'number':
                                index += 1
                                got_some = True
                                n = get_number(tokens[index].text)
                                if n is not None:
                                    if text == 'day':
                                        if self.freq == 'monthly' or (self.freq == 'yearly' and self.bymonth):
                                            self.bymonthday.append(str(n))
                                        else:
                                            self.byyearday.append(str(n))
                                            self.freq = 'yearly'
                                    else:
                                        self.byweekno.append(str(n))
                                        self.freq = 'yearly'
                                if index >= len(tokens): break
                            else:
                                break
                        if got_some:
                            index += 1
                            continue
                    # we assume a bare unit (grow up...) always specifies the frequency
                    if tokens[index].text != 'day' or \
                      (self.freq != 'weekly' and self.freq != 'monthly' and self.freq != 'yearly'):   # Issue #18: Handle every year on the 40th day; every month on the 20th day
                        self.freq = get_unit_freq(tokens[index].text)
                elif tokens[index].type_ == 'recurring_unit':   # weekly, monthly, yearly
                    self.freq = tokens[index].text
                elif tokens[index].type_ == 'ordinal':
                    ords = [get_ordinal_index(tokens[index].text)]

                    # grab all iterated ordinals (e.g. 1st, 3rd and 4th of
                    # november)
                    while index + 1 < len(tokens) and tokens[index + 1].type_ == 'ordinal':
                        ords.append(get_ordinal_index(tokens[index + 1].text))
                        index += 1

                    if index + 2 < len(tokens) and tokens[index + 1].type_ == 'unit' and \
                            tokens[index + 1].text == 'day' and tokens[index + 2].type_ == 'unit':  # Issue #18
                        index += 1      # Issue #18: Handle "first day of month" or "last day of month"

                    if index + 1 < len(tokens) and (tokens[index + 1].type_ == 'DoW' or tokens[index + 1].type_ == 'plural_weekday'):
                        # "first wednesday of/in ..."
                        dow = get_DoW(tokens[index + 1].text)[0]
                        self.ordinal_weekdays.extend( ['%s%s' % (i, dow) for i in ords] )
                        index += 1
                        if index >= len(tokens): break
                        index += 1
                        continue
                    elif index + 1 < len(tokens) and  tokens[index + 1].type_ == 'number':
                        # e.g. the 4th of every 3 months
                        n = get_number(tokens[index + 1].text)
                        if n is not None:
                            self.interval = n
                        index += 1
                    if index + 1 < len(tokens) and tokens[index + 1].type_ == 'unit' and \
                      tokens[index + 1].text == 'day' and \
                      (self.freq == 'monthly' or self.freq == 'yearly' or self.freq == 'weekly'):
                        index += 1                      # Issue #18: Handle every year on the 4th day
                    if index + 1 < len(tokens) and tokens[index + 1].type_ == 'unit':
                        # "first of the month/year"
                        self.freq = get_unit_freq(tokens[index + 1].text)
                        if self.freq == 'monthly':
                            self.bymonthday.extend([str(i) for i in ords])
                        elif self.freq == 'yearly':
                            self.byyearday.extend([str(i) for i in ords])
                        elif self.freq == 'weekly':
                            self.weekdays.extend([ordered_weekday_codes[i%8] for i in ords])
                        index += 1
                        if index >= len(tokens): break
                    elif index + 1 < len(tokens) and tokens[index + 1].type_ == 'MoY':    # 2nd of Mar
                        if not self.freq:
                            self.freq = 'yearly'
                        self.bymonth.append(str(get_MoY(tokens[index + 1].text)))
                        self.bymonthday.extend([str(i) for i in ords])
                        index += 1
                    elif index + 1 < len(tokens) and tokens[index + 1].type_ == 'instances':    # 3rd instance of ...
                        self.bysetpos.extend([str(i) for i in ords])
                        index += 1
                    elif self.freq is not None:     # Already have the freq, e.g. every month on the 4th
                        if self.freq == 'monthly':
                            self.bymonthday.extend([str(i) for i in ords])
                        elif self.freq == 'yearly':
                            self.byyearday.extend([str(i) for i in ords])
                        elif self.freq == 'weekly':
                            self.weekdays.extend([ordered_weekday_codes[i%8] for i in ords])
                    elif len(ords) == 1 and ords[0] == 2:   # Issue #16: 'second' is ambiguous - treat here as unit
                        self.freq = 'secondly'              # Issue #16
                elif tokens[index].type_ == 'DoW' or tokens[index].type_ == 'plural_weekday':
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
                    while True:
                        if index + 1 < len(tokens) and tokens[index + 1].type_ == 'ordinal':    # Aug 1st
                            self.bymonthday.append(str(get_ordinal_index(tokens[index + 1].text)))
                            index += 1
                            if index >= len(tokens): break
                        elif index + 1 < len(tokens) and tokens[index + 1].type_ == 'number':   # Issue #15: Aug 30
                            index += 1
                            n = get_number(tokens[index].text)
                            if n is not None:
                                self.bymonthday.append(str(n))
                            if index >= len(tokens): break
                        else:
                            break
                index += 1
            return True
        # No recurring match, return false
        return False

    def parse_singleton(self, s):
        """Handle singleton dates like "first monday in Aug" or "40th day in 2010" """
        try:
            tokens = Tokenizer(s)
            tokens = self.handle_Nth_to_the_last(tokens)        # Issue #18
            tokens = [t for t in tokens if t.type_ in [x[0] for x in Tokenizer.CONTENT_TYPES] ]
            if not tokens:
                return None
            if len(tokens) < 2 or len(tokens) > 5:
                return None
            if tokens[0].type_ != 'ordinal':
                return None
            if tokens[1].type_ == 'ordinal':
                return None             # e.g. "2nd and 4th"
            now_date = self.now_date
            if tokens[-1].type_ == 'number':      # year, or it could be the time
                yr = get_number(tokens[-1].text)
                if yr >= 1000:
                    now_date = datetime.datetime(yr, 1, 1)
                del tokens[-1]
            if tokens[-1].type_ == 'MoY':       # First Mon in Aug
                if (tokens[-2].type_ != 'ordinal' and tokens[-2].type_ != 'DoW') or len(tokens) > 4:
                    return None
                s = ' '.join(t.text for t in tokens)
            elif tokens[-1].type_ == 'unit' and tokens[-1].text != 'day':    # first of the year
                if len(tokens) > 4:
                    return None
                units = tokens[-1].text
                s = ' '.join(t.text for t in tokens[:-1])
                s += ' of the ' + units     # We do this so "every first year" doesn't get changed to "every 1 years"
            elif tokens[-1].text == 'day':      # 40th day in 2010
                if len(tokens) >= 3:
                    return None
                s = f'{tokens[0].text} of the year'
            else:
                return None

            s = re.sub(r'[-]([a-z0-9]+)', r'\1 last', s)        # Issue #18: change "-2nd" back to "2nd last"

            r = RecurringEvent(now_date=now_date, preferred_time_range=self.preferred_time_range)
            rfc = r.parse(f'every {s}')
            if not rfc:
                return None     # pragma nocover
            from dateutil.rrule import rrulestr
            rr = rrulestr(rfc, dtstart=now_date)
            return rr[0]
        except Exception as e:      # pragma nocover
            log.debug(f'parse_singleton({s}): Exception {e}')

        return None                 # pragma nocover

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
        if hr == 0: return 0 # ignore preferred_time_range when 0, 0 is never 12:00
        if hr < self.preferred_time_range[0]:
            return hr + 12

        return hr


    def format(self, rrule_or_datetime):
        """Convert a rrule, rrulestr, or datetime back to the appropriate English representation"""
        if rrule_or_datetime is None:
            return None
        if isinstance(rrule_or_datetime, datetime.date):    # date or datetime
            if not isinstance(rrule_or_datetime, datetime.datetime) or \
              rrule_or_datetime.time() == datetime.time(0):
                return rrule_or_datetime.strftime('%a %b %d, %Y').replace(' 0', ' ')
            elif rrule_or_datetime.minute == 0 and rrule_or_datetime.second == 0:
                return rrule_or_datetime.strftime('%a %b %d, %Y %I%p').replace(' 0', ' ').replace('AM', 'am').replace('PM', 'pm')
            elif rrule_or_datetime.second == 0:
                return rrule_or_datetime.strftime('%a %b %d, %Y %I:%M%p').replace(' 0', ' ').replace('AM', 'am').replace('PM', 'pm')
            else:
                return rrule_or_datetime.strftime('%a %b %d, %Y %I:%M:%S%p').replace(' 0', ' ').replace('AM', 'am').replace('PM', 'pm')

        def number_suffix(n):
            if n == -1:
                return 'last'
            elif n < 0:
                return number_suffix(-n) + ' to the last'
            digit = n % 10
            if digit in (0, 4, 5, 6, 7, 8, 9):
                return str(n) + 'th'
            elif digit == 1:
                return str(n) + 'st'
            elif digit == 2:
                return str(n) + 'nd'
            elif digit == 3:
                return str(n) + 'rd'

        def every_fr_interval_name(fr, n):
            result = 'every'
            suffix = fr.lower().replace('ly', '').replace('dai', 'day')
            if n <= 1:
                if suffix == 'day':
                    return 'daily'
                return result + ' ' + suffix
            elif n == 2:
                return f'{result} other {suffix}'
            else:
                return f'{result} {n} {suffix}s'

        def byday_name(bd):
            if bd is None:
                return ''   # pragma nocover
            try:
                if len(bd) == 4:
                    if bd[0] == '+':
                        bd = bd[1:]
                    elif bd[0] == '-':
                        if bd[1] == '1':
                            return 'last ' + day_names[bd[2:]]
                        else: 
                            return number_suffix(int(bd[1])) + ' to the last ' + day_names[bd[2:]]

                if len(bd) == 3:
                    return number_suffix(int(bd[0])) + ' ' + day_names[bd[1:]]
                elif len(bd) == 2:
                    return day_names[bd]
            except Exception as e:
                log.debug(f'byday_name({bd}): Exception {e}')
                raise
            return bd       # pragma nocover

        def byday_squasher(s):
            """Change 1st Fri and 2nd Fri and 3rd Fri => 1st and 2nd and 3rd Fri"""
            if s is None:
                return s    # pragma nocover
            re_squasher = re.compile(r'((?:\d.. to the )?last|\d..)\s(Mon|Tue|Wed|Thu|Fri|Sat|Sun) and ((?:\d.. to the )?last|\d..)\s\2')
            while True:
                t = re.sub(re_squasher, r'\1 and \3 \2', s)
                if t == s:
                    return t
                s = t

        def toint(v):
            try:
                return int(v)
            except Exception:
                pass
            return v

        def todatetime(v):
            if not v:
                return v
            try:
                if isinstance(v, int):
                    if v >= 10000000:
                        return todatetime(str(v))   # YYYYmmdd
                    else:
                        return v
                if 'T' in v and v[0].isdigit():
                    return datetime.datetime.strptime(v, '%Y%m%dT%H%M%S')
                elif v[0].isdigit() and len(v) == 8:
                    return datetime.datetime.strptime(v, '%Y%m%d').date()
            except Exception as e:
                log.debug(f'todatetime({v}): Exception {e}')
                pass
            return v

        def list_handler(func, lst, join_str=' and '):
            if isinstance(lst, list):
                result = join_str.join(map(func, lst))
            else:
                result = func(lst)
            log.debug(f'list_handler({func.__name__}, {lst}, {join_str}) = {result}')
            return result

        def month_name(n):
            try:
                return calendar.month_abbr[n]
            except Exception:       # pragma nocover
                return str(n)

        def parse_rrule(r):
            """Sample:
            DTSTART:19970930T090000
            RRULE:FREQ=MONTHLY;COUNT=10;BYMONTHDAY=1,-1
            EXDATE:19960402T010000,19960403T010000,19960404T010000
            """
            r = str(r)      # If it's an rrule, convert to the string representation
            result = {}
            elements = r.split('\n')
            for element in elements:
                if ':' in element:
                    name, values = element.split(':')
                else:
                    name = element
                    values = ''

                vls = {}
                for value in values.split(';'):
                    if '=' in value:
                        k, v = value.split('=')
                        v = todatetime(toint(v))
                        if isinstance(v, str) and ',' in v:
                            l = []
                            for e in v.split(','):
                                e = todatetime(toint(e))
                                l.append(e)
                            v = l
                        vls[k] = v
                    else:
                        vls[value] = None
                if len(vls) == 1 and list(vls.values())[0] is None:
                    vls = list(vls.keys())[0]
                    if isinstance(vls, str) and ',' in vls:
                        l = []
                        for e in vls.split(','):
                            e = todatetime(toint(e))
                            l.append(e)
                        vls = l
                    else:
                        vls = todatetime(toint(vls))
                result[name] = vls
            log.debug(f'parse_rrule({r}) = {result}')
            return result

        result = ''
        try:
            if isinstance(rrule_or_datetime, dict):
                pr = rrule_or_datetime      # Already parsed
            else:
                pr = parse_rrule(rrule_or_datetime)
            if 'RRULE' not in pr:
                return str(rrule_or_datetime)
            rr = pr['RRULE']
            if 'FREQ' not in rr:
                return str(rrule_or_datetime)
            fr = rr['FREQ']
            interval = rr.get('INTERVAL', 1)

            def add_suffix(pr):
                return add_time(pr['RRULE']) + add_start_end(pr) + add_excepts(pr)

            def add_time(rr):
                byhour = rr.get('BYHOUR')
                if byhour is None:
                    return ''
                byminute = rr.get('BYMINUTE', 0)
                tm = datetime.time(byhour, byminute)
                if byminute == 0:
                    return ' at' + tm.strftime(' %I%p').replace(' 0', ' ').replace('AM', 'am').replace('PM', 'pm')
                return ' at' + tm.strftime(' %I:%M%p').replace(' 0', ' ').replace('AM', 'am').replace('PM', 'pm')

            def add_start_end(pr):
                now = self.now_date.replace(microsecond=0)
                start = pr.get('DTSTART')
                rr = pr.get('RRULE')
                end = rr.get('UNTIL')
                count = rr.get('COUNT')
                result = ''
                #print(f'add_start_end({pr}), now={now}')
                adj_now = now
                interval = rr.get('INTERVAL', 1)
                freq = rr.get('FREQ')
                if freq == 'SECONDLY':
                    adj_now = now + datetime.timedelta(seconds=interval)
                elif freq == 'MINUTELY':
                    adj_now = now + datetime.timedelta(minutes=interval)
                else:
                    adj_now = now + datetime.timedelta(days=interval)

                def starting_needed():
                    """Make sure we really need this 'starting' by seeing what happens if we remove it"""
                    try:
                        from dateutil.rrule import rrulestr
                        r1 = rrulestr(rrule_or_datetime, dtstart=self.now_date)
                        r2 = rrulestr(re.sub(r'^DTSTART.*?\n', '', rrule_or_datetime, re.M), dtstart=self.now_date)
                        if r1[0] == r2[0]:
                            return False
                    except Exception:       # pragma nocover
                        pass
                    return True

                if start is not None and start != now and start != adj_now and starting_needed():
                    if end is not None:
                        result += ' from ' + self.format(start)
                        result += ' to ' + self.format(end)
                        end = None
                        count = None
                    else:
                        result += ' starting ' + self.format(start)
                if end is not None:
                    result += ' until ' + self.format(end)
                elif count is not None:
                    if count == 2:
                        result += ' twice'
                    else:
                        result += f' for {count} times'
                return result

            def squash_except_months(exdates):
                """See if we can replace a list of dates with a list of months instead"""
                months = set()
                max_year = 0
                for e in exdates:
                    months.add((e.year, e.month))
                    max_year = max(max_year, e.year)
                try:
                    from dateutil.rrule import rrulestr
                    rr = rrulestr(rrule_or_datetime, dtstart=self.now_date)
                    for r in rr:
                        if r.year > max_year:
                            break
                        if (r.year, r.month) in months: # Not excluded
                            return None
                    months = list(months)
                    months.sort()
                    return [month_name(d[1]) + ((' ' + str(d[0])) if d[0] != self.now_date.year else '') for d in months]
                except Exception:       # pragma nocover
                    return None

            def add_excepts(pr):
                exrule = pr.get('EXRULE')
                if exrule:
                    exc = self.format(dict(RRULE=exrule))
                    return ' except ' + exc
                exdates = pr.get('EXDATE')
                if not exdates:
                    return ''
                if isinstance(exdates, list) and len(exdates) > 2:
                    squash = squash_except_months(exdates)
                    if squash:
                        return ' except in ' + ' and '.join(squash)
                return ' except on ' + list_handler(self.format, exdates)

            def add_bysetpos(rr, add=' '):
                bysetpos = rr.get('BYSETPOS')
                if not bysetpos:
                    return ''
                return add + 'for the ' + list_handler(number_suffix, bysetpos) + ' instance of '

            bymonthday = rr.get('BYMONTHDAY')
            byday = rr.get('BYDAY')
            if fr == 'YEARLY':
                """        ('yearly on the fourth thursday in november', dict(freq='yearly', interval=1,byday='4TH', bymonth='11')),
                           ('every year on the fourth thursday in november', dict(freq='yearly', interval=1,byday='4TH', bymonth='11')),
                           ('once a year on december 25th', dict(freq='yearly', interval=1, bymonthday='25', bymonth='12')),
                           ('every july 4th', dict(freq='yearly', interval=1, bymonthday='4', bymonth='7')),"""
                result = every_fr_interval_name(fr, interval)
                bymonth = rr.get('BYMONTH')
                byyearday = rr.get('BYYEARDAY')
                byweekno = rr.get('BYWEEKNO')
                if bymonthday is not None and bymonth is not None:
                    if result.endswith(' year'):
                        result = result[:-5]
                    result += add_bysetpos(rr)
                    result += ' ' + list_handler(month_name, bymonth, ' or ') + ' ' + list_handler(number_suffix, bymonthday)
                    return result + add_suffix(pr)
                elif byday is not None and bymonth is not None:
                    if result.endswith(' year'):
                        result = result[:-5]
                        result += add_bysetpos(rr)
                        result += ' ' + byday_squasher(list_handler(byday_name, byday)) + ' in ' + list_handler(month_name, bymonth, ' or ')
                    else:
                        result += add_bysetpos(rr)
                        result += ' on the ' + byday_squasher(list_handler(byday_name, byday)) + ' in ' + list_handler(month_name, bymonth, ' or ')
                    return result + add_suffix(pr)
                elif byyearday is not None:
                    result += add_bysetpos(rr)
                    result += ' on the ' + list_handler(number_suffix, byyearday) + ' day'
                    return result + add_suffix(pr)
                elif byday is not None and byweekno is not None:
                    if result.endswith(' year'):
                        result = result[:-5]
                        result += add_bysetpos(rr)
                        result += ' ' + byday_squasher(list_handler(byday_name, byday)) + ' in week ' + list_handler(str, byweekno)
                    else:
                        result += add_bysetpos(rr)
                        result += ' on ' + byday_squasher(list_handler(byday_name, byday)) + ' in week ' + list_handler(str, byweekno)
                    return result + add_suffix(pr)
                elif byweekno is not None:
                    result += add_bysetpos(rr)
                    result += ' in week ' + list_handler(str, byweekno)
                    return result + add_suffix(pr)
            elif fr == 'MONTHLY':
                """ ('every 4th of the month', dict(freq='monthly', interval=1, bymonthday='4')),
                    ('every 4th and 10th of the month', dict(freq='monthly', interval=1, bymonthday='4,10')),
                    ('every first friday of the month', dict(freq='monthly', interval=1, byday='1FR')),
                    ('first friday of every month', dict(freq='monthly', interval=1, byday='1FR')),
                    ('first friday of each month', dict(freq='monthly', interval=1, byday='1FR')),
                    ('first and third friday of each month', dict(freq='monthly', interval=1, byday='1FR,3FR')),
                """
                if bymonthday is not None:
                    return add_bysetpos(rr, add='') + list_handler(number_suffix, bymonthday) + \
                            ' of ' + \
                            every_fr_interval_name(fr, interval) + \
                            add_suffix(pr)
                elif byday is not None:
                    return add_bysetpos(rr, add='') + byday_squasher(list_handler(byday_name, byday)) + ' of ' +  every_fr_interval_name(fr, interval) + add_suffix(pr)

            elif fr == 'WEEKLY':
                """     ('tuesdays', dict(freq='weekly', interval=1, byday='TU')),
                        ('weekends', dict(freq='weekly', interval=1, byday='SA,SU')),
                        ('every weekday', dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR')),
                        ('tuesdays and thursdays', dict(freq='weekly', interval=1, byday='TU,TH')),
                        ('weekly on wednesdays', dict(freq='weekly', interval=1, byday='WE')),
                        ('weekly on wednesdays and fridays', dict(freq='weekly', interval=1, byday='WE,FR')),
                        ('every sunday and saturday', dict(freq='weekly', interval=1, byday='SU,SA')),
                        ('every wed', dict(freq='weekly', interval=1, byday='WE')),
                        ('every week on tues', dict(freq='weekly', interval=1, byday='TU')),
                        ('every 3 weeks on mon', dict(freq='weekly', interval=3, byday='MO')),
                """
                if byday is not None:
                    result = every_fr_interval_name(fr, interval) + add_bysetpos(rr) + ' on ' + \
                            list_handler(byday_name, byday).replace('Sat and Sun', 'weekend'). \
                            replace('Mon and Tue and Wed and Thu and Fri', 'weekday') + add_suffix(pr)
                    result = result.replace('every week on ', 'every ')
                    result = re.sub(r'^every weekend$', 'weekends', result)
                    result = re.sub(r'^every weekday$', 'weekdays', result)
                    return result

            elif fr in ('DAILY', 'HOURLY', 'MINUTELY', 'SECONDLY'):
                """
                        ('every day', dict(freq='daily', interval=1)),
                        ('every other day', dict(freq='daily', interval=2)),
                        ('every other hour', dict(freq='hourly', interval=2)),
                """
                return every_fr_interval_name(fr, interval) + add_bysetpos(rr) + add_suffix(pr)
            else: 
                log.debug(f'format({rrule_or_datetime}): Case not handled!')
        except Exception as e:
            log.debug(f'format({rrule_or_datetime}): Exception {e}')
            #traceback.print_exc()

        return rrule_or_datetime
