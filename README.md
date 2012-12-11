# recurrent
recurrent is a python library for natural language parsing of recurring
events. It turns strings like "every tuesday and thurs until next month"
into [RFC-compliant RRULES][1], to be fed into a calendar api or [python-dateutil's][2]
rrulestr.

## usage
<pre>
>>> import datetime
>>> from recurrent import RecurringEvent
>>> r = RecurringEvent(now_date=datetime.datetime(2010, 1, 1))
>>> r.parse('every day starting next tuesday until feb')
'DTSTART:20100105\nRRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20100201'
>>> r.is_recurring
True
>>> r.get_params()
{'dtstart': '20100105', 'freq': 'daily', 'interval': 1, 'until': '20100201'}

>>> r.parse('feb 2nd')
datetime.datetime(2010, 2, 2, 0, 0)

>>> r.parse('not a date at all')
>>>
</pre>

You can then use python-dateutil to work with the recurrence rules.
<pre>
>>> from dateutil import rrule
>>> rr = rrule.rrulestr(r.get_RFC_rrule())
>>> rr.after(datetime.datetime(2010, 1, 2))
datetime.datetime(2010, 1, 5, 0, 0)
>>> rr.after(datetime.datetime(2010, 1, 25))
datetime.datetime(2010, 1, 26, 0, 0)
</pre>

## dependencies
recurrent uses [parsedatetime][3] to parse dates. If you grab the pypi
version of parsedatetime though, some tests in recurrent will fail due
to a bug with manually setting the "now" time. For some use cases this won't be an
issue, but if you need this functionality before it's patched you can grab
[my fork][4] of parsedatetime.

## examples
* on weekdays
* every fourth of the month from jan 1 2010 to dec 25th 2020
* each thurs until next month
* once a year on the fourth thursday in november
* tuesdays and thursdays

Take a look at the tests for more.

## things it can't do

recurrent is regrettably quite U.S. (and completely english) centric. Contributions from other perspectives are welcome :)

## credits
recurrent is inspired by the similar Ruby library Tickle by Joshua
Lippiner. It also uses the parsedatetime library for fuzzy human date
parsing.

[1]: http://www.kanzaki.com/docs/ical/rrule.html
[2]: http://labix.org/python-dateutil
[3]: http://code.google.com/p/parsedatetime
[4]: https://github.com/kvh/parsedatetime
