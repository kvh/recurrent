# Recurrent
Recurrent is a python library for natural language parsing and formatting of dates and recurring
events. It turns strings like "every tuesday and thurs until next month"
into [RFC-compliant RRULES][1], to be fed into a calendar api or [python-dateutil's][2]
rrulestr.  It will also accept such rrules and return a natural language representation of them.

```sh
pip install recurrent
```

## Examples
### Date times
* next tuesday
* tomorrow
* in an hour
* in 15 mins
* Mar 4th at 9am
* 3rd Thu in Apr at 10 o'clock
* 40th day of 2020

### Recurring events
* on weekdays
* every fourth of the month from jan 1 2010 to dec 25th 2020
* each thurs until next month
* once a year on the fourth thursday in november
* tuesdays and thursdays at 3:15
* wednesdays at 9 o'clock
* fridays at 11am
* daily except in June
* daily except on June 23rd and July 4th
* every monday except each 2nd monday in March
* fridays twice
* fridays 3x
* every other friday for 5 times
* every 3 fridays from november until february
* fridays starting in may for 10 occurrences
* tuesdays for the next six weeks
* every Mon-Wed for the next 2 months
* every Mon thru Wed for the next year
* every other Fri for the next three years
* monthly on the first and last instance of wed and fri
* every Tue and Fri in week 14
* every year on Dec 25

### Messy strings
* Please schedule the meeting for every other tuesday at noon
* Set an alarm for next tuesday at 11pm

## Usage
```python
>>> import datetime
>>> from recurrent.event_parser import RecurringEvent
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

>>> r.format('DTSTART:20100105\nRRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20100201')
'daily from Tue Jan 5, 2010 to Mon Feb 1, 2010'
>>> r.format(r.parse('fridays twice'))
'every Fri twice'
>>>
```

You can then use python-dateutil to work with the recurrence rules.
```python
>>> from dateutil import rrule
>>> rr = rrule.rrulestr(r.get_RFC_rrule())
>>> rr.after(datetime.datetime(2010, 1, 2))
datetime.datetime(2010, 1, 5, 0, 0)
>>> rr.after(datetime.datetime(2010, 1, 25))
datetime.datetime(2010, 1, 26, 0, 0)
```

## Dependencies
Recurrent uses [parsedatetime][3] to parse dates and [python.dateutil][2] if available to optimize some results.

## Things it can't do

Recurrent is regrettably quite U.S. (and completely english) centric. Contributions from other perspectives are welcome :)

## Credits
Recurrent is inspired by the similar Ruby library Tickle by Joshua
Lippiner. It also uses the parsedatetime library for fuzzy human date
parsing.  The handling of COUNT, BYSETPOS, BYWEEKNO, EXDATE and EXRULE,
and the format function was supplied by Joe Cool snoopyjc@gmail.com 
https://github.com/snoopyjc

## Author
Ken Van Haren [@squaredloss](http://twitter.com/squaredloss)

[1]: http://www.kanzaki.com/docs/ical/rrule.html
[2]: https://pypi.org/project/python-dateutil
[3]: https://github.com/bear/parsedatetime
[4]: https://github.com/kvh/parsedatetime
