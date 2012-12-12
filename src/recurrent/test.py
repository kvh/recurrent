import unittest
import datetime

from event_parser import RecurringEvent

NOW = datetime.datetime(2010, 1, 1)

expressions = [
        # recurring events
        ('daily', dict(freq='daily', interval=1)),
        ('each day', dict(freq='daily', interval=1)),
        ('everyday', dict(freq='daily', interval=1)),
        ('every other day', dict(freq='daily', interval=2)),
        ('tuesdays', dict(freq='weekly', interval=1, byday='TU')),
        ('weekends', dict(freq='weekly', interval=1, byday='SA,SU')),
        ('weekdays', dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR')),
        ('every weekday', dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR')),
        ('tuesdays and thursdays', dict(freq='weekly', interval=1, byday='TU,TH')),
        ('weekly on wednesdays', dict(freq='weekly', interval=1, byday='WE')),
        ('weekly on wednesdays and fridays', dict(freq='weekly', interval=1, byday='WE,FR')),
        ('every sunday and saturday', dict(freq='weekly', interval=1, byday='SU,SA')),
        ('every wed', dict(freq='weekly', interval=1, byday='WE')),
        ('every wed.', dict(freq='weekly', interval=1, byday='WE')),
        ('every wednsday', dict(freq='weekly', interval=1, byday='WE')),
        ('every week on tues', dict(freq='weekly', interval=1, byday='TU')),
        ('once a week on sunday', dict(freq='weekly', interval=1, byday='SU')),
        ('every 3 weeks on mon', dict(freq='weekly', interval=3, byday='MO')),
        ('every 3 days', dict(freq='daily', interval=3)),
        ('every 4th of the month', dict(freq='monthly', interval=1, bymonthday='4')),
        ('every 4th and 10th of the month', dict(freq='monthly', interval=1, bymonthday='4,10')),
        ('every first friday of the month', dict(freq='monthly', interval=1, byday='1FR')),
        ('first friday of every month', dict(freq='monthly', interval=1, byday='1FR')),
        ('first friday of each month', dict(freq='monthly', interval=1, byday='1FR')),
        ('first and third friday of each month', dict(freq='monthly', interval=1, byday='1FR,3FR')),
        ('yearly on the fourth thursday in november', dict(freq='yearly', interval=1,byday='4TH', bymonth='11')),
        ('every year on the fourth thursday in november', dict(freq='yearly', interval=1,byday='4TH', bymonth='11')),
        ('once a year on december 25th', dict(freq='yearly', interval=1,byday='25', bymonth='12')),

        # with start and end dates
        ('daily starting march 3rd',
                        dict(dtstart='%d0303'%NOW.year, freq='daily', interval=1)),
        ('starting tomorrow on weekends',
                        dict(dtstart='%d0102'%NOW.year, freq='weekly',
                            interval=1, byday='SA,SU')),
        ('daily starting march 3rd until april 5th',
                        dict(dtstart='%d0303'%NOW.year, until='%d0405'%NOW.year, freq='daily', interval=1)),
        ('every wed until november',
                        dict(until='%d1101'%NOW.year, freq='weekly', interval=1, byday='WE')),
        ('every 4th of the month starting next tuesday',
                        dict(dtstart=(NOW +
                            datetime.timedelta(days=(1 - NOW.weekday())%7)).strftime('%Y%m%d'),
                            freq='monthly', interval=1, bymonthday='4')),
        ('mondays and thursdays from jan 1 to march 25th',
                        dict(dtstart='%d0101'%NOW.year,
                            until='%d0325'%NOW.year,
                            freq='weekly', interval=1, byday='MO,TH')),

        # time recurrences
        ('every 5 minutes', dict(freq='minutely', interval=5)),
        ('every 30 seconds', dict(freq='secondly', interval=30)),
        ('every other hour', dict(freq='hourly', interval=2)),

        # with times
        ('daily at 3pm', dict(freq='daily', interval=1, byhour='15', byminute='0')),
        ('daily at 3:00pm', dict(freq='daily', interval=1, byhour='15', byminute='0')),

        # TODO
        #('saturday through tuesday', dict(freq='daily', interval=1, byday='SA,SU,MO,TU')),
        #('every thursday for the next three weeks', dict(freq='weekly',
        #    interval=1, count=3, byday='TH')),

        # non-recurring
        ('march 3rd', datetime.datetime(NOW.year, 3, 3).date()),
        ('tomorrow', datetime.datetime(NOW.year, NOW.month, NOW.day +
            1).date()),

        # pdt fucks this up, does feb 18 first, then adjusts thurs
        ('thursday, february 18th', datetime.datetime(NOW.year, 2,
            18).date()),
        ('mar 2 2012', datetime.datetime(2012, 3, 2).date()),

        # pdt fucks this up, assumes "this" sunday is "the one after this"
        ('this sunday', (NOW + datetime.timedelta(days=(6 -
                                NOW.weekday())%7)).date()),

        # non-dates
        ('not a date at all', dict(freq=None, interval=None, bymonthday=None)),
        ('cancel', dict(freq=None, interval=None, bymonthday=None)),
        ]

time_expressions = [
        ('march 3rd at 12:15am', datetime.datetime(NOW.year, 3, 3, 0, 15)),
        ('tomorrow at 3:30', datetime.datetime(NOW.year, NOW.month, NOW.day +
            1, 15, 30)),
        ('in 30 minutes', NOW.replace(minute=NOW.minute + 30)),
        ('at 4', NOW.replace(hour=16)),
        ('2 hours from now', NOW.replace(hour=NOW.hour + 2)),

        ('sunday at 2', (NOW + datetime.timedelta(days=(6 -
            NOW.weekday())%7)).replace(hour=14)),
]
expressions += time_expressions

ambiguous_expressions = (
        ('weekly', dict(freq='weekly', interval=1)),
        ('twice weekly', dict(freq='weekly', interval=1)),
        ('three times a week', dict(freq='weekly', interval=1)),
        ('monthly', dict(freq='monthly', interval=1)),
        ('once a month', dict(freq='monthly', interval=1)),
        ('yearly', dict(freq='yearly', interval=1)),
        )

non_dt_expressions = (
        ('Once in a while.'),
        ('Every time i hear that i apreciate it.'),
        ('Once every ones in'),

        # failing
        # not sure what pdt does here
        ('first time for everything. wait a minute'),
        # parses as may
        ('may this test pass.'),
        )

embedded_expressions = [('im available ' + s, v) for s,v in expressions] + [
        (s + ' would work best for me', v) for s,v in expressions] + [
        ('remind me to move car ' + s + ' would work best for me', v) for s,v in expressions]

expressions += embedded_expressions
expressions += [(e, None) for e in non_dt_expressions]


class ParseTest(unittest.TestCase):

    def test_return_recurring(self):
        string = 'every day'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, str))

    def test_return_non_recurring(self):
        string = 'march 3rd, 2001'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_recurring2(self):
        string = 'next wednesday'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_date(self):
        string = 'remember to call mitchell'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertFalse(ret)

    def test_rrule_string(self):
        string = 'every day starting feb 2'
        date = RecurringEvent(NOW)
        date.parse(string)
        expected = """DTSTART:20100202\nRRULE:FREQ=DAILY;INTERVAL=1"""
        self.assertEqual(expected, date.get_RFC_rrule())


def test_expression(string, expected_params):
    def test_(self):
        date = RecurringEvent(NOW)
        val = date.parse(string)
        if expected_params is None:
            self.assertTrue(val is None or date.get_params().keys() == ['interval'],
                        "Non-date error: '%s' -> '%s', expected '%s'"%(
                            string, val, expected_params))
            return
        if isinstance(expected_params, datetime.datetime) or isinstance(expected_params, datetime.date):
            if isinstance(expected_params, datetime.datetime):
                self.assertEqual(val, expected_params,
                        "Date parse error: '%s' -> '%s', expected '%s'"%(
                            string, val, expected_params))
                return
            self.assertEqual(val.date(), expected_params,
                        "Date parse error: '%s' -> '%s', expected '%s'"%(
                            string, val, expected_params))
            return
        actual_params = date.get_params()
        for k, v in expected_params.items():
            av = actual_params.pop(k, None)
            self.assertEqual(av, v,
                    "Rule mismatch on rule '%s' for '%s'. Expected %s, got %s\nRules: %s" % (k, string, v, av,
                        date.get_params()))
        # make sure any extra params are empty/false
        for k, v in actual_params.items():
            self.assertFalse(v)
    return test_

# add a test for each expression
for i, expr in enumerate(expressions):
    string, params = expr
    setattr(ParseTest, 'test_%02d' % i, test_expression(string, params))


if __name__ == '__main__':
    print "Dates relative to %s" % NOW
    unittest.main(verbosity=2)
