# -*- coding: utf-8 -*-

import local_settings
from ecobee import core

# Get configuration variables
thermostat_name = local_settings.thermostat_name
days_to_set = local_settings.days_to_set
new_climates = local_settings.climates.split(',')
supercool_values = local_settings.supercool_values
timeofuse_days = local_settings.timeofuse_day_range
timeofuse_restricted = local_settings.timeofuse_restricted
supercool_month_range = local_settings.supercool_month_range
supercool_cutoff = local_settings.supercool_low_temp_cutoff
timeofuse_holidays = local_settings.timeofuse_holidays
timeofuse_holidays_cool_temp = local_settings.timeofuse_holidays_cool_temp
timeofuse_holidays_start_time = local_settings.timeofuse_holidays_start_time
timeofuse_holidays_end_time = local_settings.timeofuse_holidays_end_time
notify = local_settings.notifications_enabled

# Authenticate and get thermostat list
thermostat = core.Ecobee(ecobee_service=core.authenticate(thermostat_name),
                         timeofuse_days=timeofuse_days,
                         timeofuse_restricted=timeofuse_restricted,
                         days_to_set=days_to_set,
                         supercool_cutoff=supercool_cutoff,
                         new_climate_prefixes=new_climates,
                         supercool_values=supercool_values,
                         supercool_months=supercool_month_range)

# Get unique climate names for each day and create climates
thermostat.set_new_climate_names(create=True, notify=notify)

# Get program values based on outdoor high temp
program_values = thermostat.get_program_values(notify=notify)

# Update program climates
thermostat.set_thermostat_climates(program=program_values, update=True, notify=notify)

# Update schedule
thermostat.set_thermostat_schedule(program=program_values, update=True, notify=notify)

# Create vacations for off-peak holidays
if len(timeofuse_holidays) > 0:
    for holiday_date in timeofuse_holidays.split(','):
        thermostat.create_vacation(name=holiday_date,
                                   start_date=f"{holiday_date} {timeofuse_holidays_start_time}",
                                   end_date=f"{holiday_date} {timeofuse_holidays_end_time}",
                                   cool_temp=timeofuse_holidays_cool_temp)

# ToDo: How will I undo the supercool schedule and climates outside supercool months?
# ToDo: How to handle transitional months where some days don't meet the supercool threshold?
