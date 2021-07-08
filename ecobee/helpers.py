# -*- coding: utf-8 -*-

import calendar
import local_settings
from datetime import datetime, timedelta
from ecobee import notifications, logger


def get_time_slot(start_time, end_time=''):
    date_format = '%H:%M'

    schedule_start = datetime.strptime('00:00', date_format)  # compare to beginning of the day
    start_time = datetime.strptime(start_time, date_format)
    if not end_time:
        end_time = start_time + timedelta(minutes=30)
    else:
        end_time = datetime.strptime(end_time, date_format)
        if end_time < start_time:
            raise Exception('End time can not be before start time')

    start_slot = ((start_time - schedule_start).seconds / 60 / 60 / .5)
    end_slot = ((end_time - schedule_start).seconds / 60 / 60 / .5)
    if start_slot.is_integer() and end_slot.is_integer():
        return int(start_slot), int(end_slot)


def get_day_number(day):
    # Verify friendly name
    if day.lower() == 'tomorrow':
        return (datetime.today() + timedelta(days=1)).weekday()

    # Day number check
    if day.isdigit():
        daynum = int(day)
        if 0 <= daynum <= 6:
            return daynum

    # Support long and abbreviated day names
    [daynum] = [i for i, value in enumerate(calendar.day_name) if value.lower() == day.lower()] or [None]
    if daynum is None:
        [daynum] = [i for i, value in enumerate(calendar.day_abbr) if value.lower() == day.lower()] or [None]
    return daynum


def get_day_slots(days):
    day_set = set()
    for day in days.split(','):
        if day.lower() == 'weekdays':
            day_set.update([0, 1, 2, 3, 4])
        elif day.lower() == 'weekend':
            day_set.update([5, 6])
        elif day.lower() == 'tomorrow':
            day_set.add((datetime.today() + timedelta(days=1)).weekday())
        else:
            daynum = get_day_number(day)
            if daynum not in day_set:
                day_set.add(daynum)
    return list(day_set)


def get_day_name(daynum):
    return calendar.day_name[daynum]


def send_notifications(title, message):
    if local_settings.email_enabled:
        logger.info(u"Sending Email notification")
        email_to = local_settings.email_to
        email = notifications.Email()
        email.notify(email_to, title, message)
    if local_settings.pushbullet_enabled:
        logger.info(u"Sending PushBullet notification")
        pushbullet = notifications.PUSHBULLET()
        pushbullet.notify(title, message)
    if local_settings.pushover_enabled:
        logger.info(u"Sending Pushover notification")
        prowl = notifications.PUSHOVER()
        prowl.notify(title, message)
    if local_settings.join_enabled:
        logger.info(u"Sending Join notification")
        join = notifications.JOIN()
        join.notify(title, message)


def get_range_from_string(x):
    result = []
    low, high = x.split('-')
    low, high = int(low), int(high)
    result.extend([low, high])
    return result
