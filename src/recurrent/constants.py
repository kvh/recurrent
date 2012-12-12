import re

DoWs = (
    r'mon(day)?',
    r'tues?(day)?',
    r'(we(dnes|nds|ns|des)day)|(wed)',
    r'(th(urs|ers)day)|(thur?s?)',
    r'fri(day)?',
    r'sat([ue]rday)?',
    r'sun(day)?',
    r'weekday',
    r'weekend'
)
RE_DOWS = [re.compile(r) for r in DoWs]
RE_PLURAL_DOW = re.compile('|'.join( ['mondays', 'tuesdays', 'wednesdays',
    'thursdays', 'fridays', 'saturdays', 'sundays']))
RE_DOW = re.compile('(' + ')|('.join(DoWs) + ')')
RE_PLURAL_WEEKDAY = re.compile('weekdays|weekends|%s'%RE_PLURAL_DOW.pattern)
weekday_codes = [ 'MO','TU','WE','TH','FR', 'SA', 'SU', 'MO,TU,WE,TH,FR',
'SA,SU']

MoYs = (
    r'jan(uary)?',
    r'feb(r?uary)?',
    r'mar(ch)?',
    r'apr(il)?',
    r'may',
    r'jun(e)?',
    r'jul(y)?',
    r'aug(ust)?',
    r'sept?(ember)?',
    r'oct(ober)?',
    r'nov(ember)?',
    r'dec(ember)?',
)
RE_MOYS = [re.compile(r + '$') for r in MoYs]
RE_MOY = re.compile('(' + ')$|('.join(MoYs) + ')$')

units = ['day', 'week', 'month', 'year', 'hour', 'minute', 'seconds']
units_freq = ['daily', 'weekly', 'monthly', 'yearly', 'hourly', 'minutely', 'secondly']
RE_UNITS = re.compile(r'^(' + 's?|'.join(units) + '?)$')

ordinals = (
    r'first',
    r'second',
    r'third',
    r'fourth',
    r'fifth',
    r'sixth',
    r'seventh',
    r'eighth',
    r'ninth',
    r'tenth',
    )
RE_ORDINALS = [re.compile(r + '$') for r in ordinals]
RE_ORDINAL = re.compile(r'\d+(st|nd|rd|th)$|' + '$|'.join(ordinals))
numbers = (
    r'zero',
    r'one',
    r'two',
    r'three',
    r'four',
    r'five',
    r'six',
    r'seven',
    r'eight',
    r'nine',
    r'ten',
    )
RE_NUMBERS = [re.compile(r + '$') for r in numbers]
RE_NUMBER = re.compile('(' + '|'.join(numbers) + ')$|(\d+)$')

RE_EVERY = re.compile(r'(every|each|once)$')

RE_THROUGH = re.compile(r'(through|thru)$')

RE_DAILY = re.compile(r'daily|everyday')
RE_RECURRING_UNIT = re.compile(r'weekly|monthly|yearly')

# getters
def get_number(s):
    try:
        return int(s)
    except ValueError:
        return numbers.index(s)

def get_ordinal_index(s):
    try:
        return int(s[:-2])
    except ValueError:
        pass
    for i, reg in enumerate(RE_ORDINALS):
        if reg.match(s):
            return i + 1
    raise ValueError

def get_DoW(s):
    for i, dow in enumerate(RE_DOWS):
        if dow.search(s):
            return weekday_codes[i].split(',')
    raise ValueError

def get_MoY(s):
    for i, moy in enumerate(RE_MOYS):
        if moy.search(s):
            return i + 1
    raise ValueError

def get_unit_freq(s):
    for i, unit in enumerate(units):
        if unit in s:
            return units_freq[i]
    raise ValueError

