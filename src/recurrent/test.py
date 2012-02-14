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


        # TODO
        ('saturday through tuesday', dict(freq='daily', interval=1, byday='SA,SU,MO,TU')),

        # non-recurring
        ('march 3rd', {}),
        ('tomorrow', {}),
        ('wednesday, february 3rd', {}),
        ('mar 2 2012', {}),
        ('next sunday', {}),


        # non-dates
        ('not a date at all', dict(freq=None, interval=None, bymonthday=None)),
        ('cancel', dict(freq=None, interval=None, bymonthday=None)),
        ]

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
        date.parse(string)
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
    unittest.main(verbosity=2)

