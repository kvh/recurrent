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
>>> parsed_result = r.parse('every day starting next tuesday until feb')
>>> parsed_result
'DTSTART:20100105\nRRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20100201'
>>> r.is_recurring
True
>>> r.get_params()
{'dtstart': '20100105', 'freq': 'daily', 'interval': 1, 'until': '20100201'}

>>> parsed_result = r.parse('feb 2nd')
>>> parsed_result
datetime.datetime(2010, 2, 2, 0, 0)

>>> parsed_result = r.parse('not a date at all')
>>> parsed_result
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
my fork of parsedatetime.

## examples
take a look at the tests.

## things it can't do
recurrent is regrettably quite U.S. (and completely english) centric for now. Contributions from other perspectives are welcome :)

## credit
recurrent is inspired by the similar Ruby library Tickle by Joshua
Lippiner. It also uses the parsedatetime library to do human date
parsing.

[1]: http://www.kanzaki.com/docs/ical/rrule.html
[2]: http://labix.org/python-dateutil
[3]: http://code.google.com/p/parsedatetime
