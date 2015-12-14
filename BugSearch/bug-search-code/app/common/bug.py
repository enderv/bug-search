__author__ = 'Chris'

import datetime
from dateutil.parser import parse as _parse_date_str
from dateutil.tz import tzutc, tzoffset



def parse_date_str(date_string):
    '''parses a date string and sets the timzone to tzutc if none is found.

    :returns: a datetime.datetime object'''
    try:
        parsed = _parse_date_str(date_string)
    except BaseException as e:
        err_string = "Failed to parse date '{}' \n {}"
        raise ValueError(err_string.format(date_string, str(e)))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tzutc())
    return parsed

def utc_now():
    '''returns a timezone-aware datetime object for the current time'''
    return datetime.datetime.utcnow().replace(tzinfo=tzutc())


def fix_null(dictionary):
    """Turns null into None"""
    for k, v in dictionary.iteritems():
        if dictionary[k] == 'null' or dictionary[k] == {}:
            dictionary[k] = None
        elif type(dictionary[k]) == dict:
            fix_null(dictionary[k])


def fix_date_str(date_string):
        parsed = parse_date_str(date_string)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tzoffset(None, 0))
        return parsed.isoformat()


def clean_bug_data(bug_data):
    """
    A function to normalize bug information to the same dictionary structure
    :returns: a normalized bug dict
    """

    fix_null(bug_data)
    if 'status' in bug_data:
        bug_data['status'] = bug_data['status'].lower()

    date = None
    for date_key in ('openedDate', 'when', 'created_at', 'created'):
        if date_key in bug_data:
            try:
                date = fix_date_str(bug_data[date_key])
                break
            except:
                pass

    bug_data['openedDate'] = date or datetime.datetime.utcnow().isoformat()
    return bug_data

