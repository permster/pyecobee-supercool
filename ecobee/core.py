# -*- coding: utf-8 -*-

import shelve
import pytz
import time
from six.moves import input
from pyecobee import *
from datetime import datetime, timedelta
from ecobee import helpers, logger
from pytz import timezone

DB_FILE = f'{helpers.get_script_dir()}/pyecobee_db'


def persist_to_shelf(ecobee_service, file_name=DB_FILE):
    logger.debug(f'Shelve file: {file_name}')
    pyecobee_db = shelve.open(file_name, protocol=2)
    pyecobee_db[ecobee_service.thermostat_name] = ecobee_service
    pyecobee_db.close()


def refresh_tokens(ecobee_service):
    token_response = ecobee_service.refresh_tokens()
    logger.debug('TokenResponse returned from ecobee_service.refresh_tokens():\n{0}'.format(
        token_response.pretty_format()))

    persist_to_shelf(ecobee_service)


def request_tokens(ecobee_service):
    token_response = ecobee_service.request_tokens()
    logger.debug('TokenResponse returned from ecobee_service.request_tokens():\n{0}'.format(
        token_response.pretty_format()))

    persist_to_shelf(ecobee_service)


def authorize(ecobee_service):
    authorize_response = ecobee_service.authorize()
    logger.debug('AuthorizeResponse returned from ecobee_service.authorize():\n{0}'.format(
        authorize_response.pretty_format()))

    persist_to_shelf(ecobee_service)

    logger.info('Please goto ecobee.com, login to the web portal and click on the settings tab. Ensure the My '
                'Apps widget is enabled. If it is not click on the My Apps option in the menu on the left. In the '
                f'My Apps widget paste "{authorize_response.ecobee_pin}" and in the textbox labelled '
                '"Enter your 4 digit pin to install your third party app" and then click "Install App". '
                'The next screen will display any permissions the app requires and will ask you to click '
                '"Authorize" to add the application.\n\nAfter completing this step please hit "Enter" to continue.')
    input()


def authenticate(thermostat_name, db_file=None):
    pyecobee_db = ecobee_service = None
    if db_file is None:
        db_file = DB_FILE
    try:
        pyecobee_db = shelve.open(db_file, protocol=2)
        ecobee_service = pyecobee_db[thermostat_name]
    except KeyError:
        application_key = input('Please enter the API key of your ecobee App: ')
        ecobee_service = EcobeeService(thermostat_name=thermostat_name, application_key=application_key)
    finally:
        try:
            pyecobee_db.close()
        except Exception as e:
            logger.error(f'Error closing shelf DB, error: {e}')

    if ecobee_service is None:
        return

    if ecobee_service.authorization_token is None:
        authorize(ecobee_service)

    if ecobee_service.access_token is None:
        request_tokens(ecobee_service)

    now_utc = datetime.now(pytz.utc)
    if now_utc > ecobee_service.refresh_token_expires_on:
        logger.info('Refresh token expired, attempting to obtain a new access token.')
        authorize(ecobee_service)
        request_tokens(ecobee_service)
    elif now_utc > ecobee_service.access_token_expires_on:
        logger.info('Access token expired, attempting to refresh the token.')
        refresh_tokens(ecobee_service)
    elif now_utc + timedelta(minutes=1) > ecobee_service.access_token_expires_on:
        logger.info('Access token expires within the next minute, attempting to refresh the token.')
        refresh_tokens(ecobee_service)

    return ecobee_service


class Ecobee:
    DEFAULT_SELECTION = Selection(selection_type=SelectionType.REGISTERED.value,
                                  selection_match='',
                                  include_program=True,
                                  include_weather=True,
                                  include_sensors=True,
                                  include_location=True,
                                  include_events=True,
                                  include_settings=True)
    DEFAULT_CLIMATE = "sleep"

    def __init__(
            self,
            ecobee_service,
            thermostat_index=None,
            thermostat_name=None,
            thermostat_identifier=None,
            thermostat_list=None,
            thermostat_object=None,
            thermostat_climates=None,
            thermostat_events=None,
            thermostat_settings=None,
            selection=None,
            thermostat_schedule=None,
            temp_high=None,
            high_temp_list=None,
            new_climate_prefixes=None,
            new_climate_names=None,
            timeofuse_days=None,
            timeofuse_restricted=True,
            days_to_set=None,
            tomorrow_daynum=None,
            thermostat_sensors=None,
            timezone=None,
            isdaylightsavings=None,
            supercool_cutoff=None,
            supercool_values=None,
            hvac_mode=None,
            supercool_months=None
    ):
        """
        Construct an Ecobee thermostat instance
        """
        if supercool_values is None:
            supercool_values = {}
        self._ecobee_service = ecobee_service
        self._selection = selection if selection is not None else self.DEFAULT_SELECTION
        if thermostat_list is not None:
            self._thermostat_list = thermostat_list
        else:
            self.thermostat_list = self.selection
        self._thermostat_name = thermostat_name if thermostat_name is not None else self.get_thermostat_name()
        self._thermostat_index = thermostat_index if thermostat_index is not None else \
            self.get_thermostat_index(name=self._thermostat_name)
        self._thermostat_identifier = thermostat_identifier if thermostat_identifier is not None else \
            self.get_thermostat_identifier(name=self._thermostat_name, index=self._thermostat_index)
        self._thermostat_object = thermostat_object if thermostat_object is not None else self.thermostat_object
        self._thermostat_climates = thermostat_climates if thermostat_climates is not None else \
            self.thermostat_climates
        self._thermostat_schedule = thermostat_schedule if thermostat_schedule is not None else \
            self.thermostat_schedule
        self._temp_high = temp_high if temp_high is not None else self.get_forecast_temp_high()
        if self._temp_high == 9999:
            logger.error('Unknown high temperature, unable to make program changes.')
        self._thermostat_events = thermostat_events if thermostat_events is not None else self.thermostat_events
        self._thermostat_settings = thermostat_settings if thermostat_settings is not None else \
            self.thermostat_settings
        self._high_temp_list = high_temp_list if high_temp_list is not None else self.get_forecast_high_temps()
        self.new_climate_prefixes = new_climate_prefixes
        self.new_climate_names = new_climate_names
        self.timeofuse_days = timeofuse_days
        self.timeofuse_restricted = timeofuse_restricted
        self.days_to_set = days_to_set
        self._tomorrow_daynum = tomorrow_daynum
        self._thermostat_sensors = thermostat_sensors if thermostat_sensors is not None else self.thermostat_sensors
        self._timezone = timezone if timezone is not None else self.timezone
        self._isdaylightsavings = isdaylightsavings if isdaylightsavings is not None else self.isdaylightsavings
        self._supercool_cutoff = supercool_cutoff if supercool_cutoff is not None else self.supercool_cutoff
        self._supercool_values = supercool_values if supercool_values is not None else self.supercool_values
        self._hvac_mode = hvac_mode if hvac_mode is not None else self.hvac_mode
        self._during_supercool_months = self.during_supercool_months = supercool_months \
            if supercool_months is not None else self.during_supercool_months

    @property
    def ecobee_service(self):
        return self._ecobee_service

    @property
    def selection(self):
        return self._selection

    @ecobee_service.setter
    def ecobee_service(self, e_service):
        self._ecobee_service = e_service

    @property
    def thermostat_list(self):
        return self._thermostat_list

    @thermostat_list.setter
    def thermostat_list(self, selection):
        self._thermostat_list = self.get_thermostats(selection)

    @property
    def thermostat_index(self):
        return self._thermostat_index

    @property
    def thermostat_name(self):
        return self._thermostat_name

    @property
    def thermostat_identifier(self):
        return self._thermostat_identifier

    @property
    def thermostat_object(self):
        return self._thermostat_list[self.thermostat_index]

    @property
    def thermostat_climates(self):
        return self._thermostat_list[self.thermostat_index].program.climates

    @property
    def thermostat_schedule(self):
        return self._thermostat_list[self.thermostat_index].program.schedule

    @property
    def thermostat_events(self):
        return self._thermostat_list[self.thermostat_index].events

    @property
    def thermostat_settings(self):
        return self._thermostat_list[self.thermostat_index].settings

    @property
    def temp_high(self):
        return self._temp_high

    @property
    def high_temp_list(self):
        return self._high_temp_list

    @property
    def new_climate_prefixes(self):
        return self._new_climate_prefixes

    @new_climate_prefixes.setter
    def new_climate_prefixes(self, value):
        self._new_climate_prefixes = value

    @property
    def new_climate_names(self):
        return self._new_climate_names

    @new_climate_names.setter
    def new_climate_names(self, value):
        self._new_climate_names = value

    @property
    def timeofuse_days(self):
        return self._timeofuse_days

    @timeofuse_days.setter
    def timeofuse_days(self, value):
        self._timeofuse_days = list(range(int(value.split('-')[0]), int(value.split('-')[1]) + 1)) \
            if value is not None else list()

    @property
    def timeofuse_restricted(self):
        return self._timeofuse_restricted

    @timeofuse_restricted.setter
    def timeofuse_restricted(self, value):
        self._timeofuse_restricted = value

    @property
    def days_to_set(self):
        return self._days_to_set

    @days_to_set.setter
    def days_to_set(self, value):
        self._days_to_set = helpers.get_day_slots(days=value) if value is not None else list()

    @property
    def tomorrow_daynum(self):
        return datetime.strptime(self._thermostat_list[self.thermostat_index].weather.forecasts[1].date_time,
                                 '%Y-%m-%d %H:%M:%S').weekday()

    @property
    def thermostat_sensors(self):
        return self._thermostat_list[self.thermostat_index].remote_sensors

    @property
    def timezone(self):
        return self._thermostat_list[self.thermostat_index].location.time_zone

    @property
    def isdaylightsavings(self):
        return self._thermostat_list[self.thermostat_index].location.is_daylight_saving

    @property
    def supercool_cutoff(self):
        return self._supercool_cutoff

    @supercool_cutoff.setter
    def supercool_cutoff(self, value):
        self._supercool_cutoff = value

    @property
    def supercool_values(self):
        return self._supercool_values

    @property
    def hvac_mode(self):
        return self._thermostat_list[self.thermostat_index].settings.hvac_mode.lower()

    @property
    def during_supercool_months(self):
        return self._during_supercool_months

    @during_supercool_months.setter
    def during_supercool_months(self, value):
        temp_list = helpers.get_range_from_string(value)
        if temp_list[0] <= datetime.now().month <= temp_list[1]:
            self._during_supercool_months = True
        else:
            self._during_supercool_months = False

    def get_thermostats(self, selection):
        thermostat_response = self._ecobee_service.request_thermostats(selection)
        if thermostat_response.status.code == 0:
            return thermostat_response.thermostat_list
        else:
            logger.error(f'Failure while executing request_thermostats:\n{thermostat_response.pretty_format()}')

    def get_thermostat_index(self, name=None, identifier=None):
        if name is not None:
            return next((idx for idx, x in enumerate(self._thermostat_list) if x.name == name), 0)
        if identifier is not None:
            return next((idx for idx, x in enumerate(self._thermostat_list) if x.identifier == identifier), 0)

        return 0

    def get_thermostat_name(self, index=None, identifier=None):
        if index is not None:
            return self._thermostat_list[index].name
        if identifier is not None:
            return next(x.name for x in self._thermostat_list if x.identifier == identifier)

        return self._thermostat_list[0].name  # Default return first name

    def get_thermostat_identifier(self, name=None, index=None):
        if index is not None:
            return self._thermostat_list[index].identifier
        if name is not None:
            return next(x.identifier for x in self._thermostat_list if x.name == name)

        return self._thermostat_list[0].identifier  # Default return first identifier

    def get_forecast_high_temps(self):
        high_temps = []
        for i in range(7):
            high_temps.append(None)

        weather_forecasts = self._thermostat_list[self.thermostat_index].weather.forecasts
        for i in range(1, 5):
            forecast_day_num = datetime.strptime(weather_forecasts[i].date_time, '%Y-%m-%d %H:%M:%S').weekday()
            high_temps[forecast_day_num] = weather_forecasts[i].temp_high

        return high_temps

    def get_forecast_temp_high(self, day='tomorrow'):
        day_num = helpers.get_day_number(day)
        weather_forecasts = self._thermostat_list[self.thermostat_index].weather.forecasts
        for forecast in weather_forecasts:
            forecast_day_num = datetime.strptime(forecast.date_time, '%Y-%m-%d %H:%M:%S').weekday()
            if forecast_day_num == day_num:
                return forecast.temp_high

        return 9999  # Ecobee provides 4 days of forecasts, if beyond 4 days this will return 9999

    def get_climate_ref(self, name):
        for climate in self.thermostat_climates:
            if climate.name.lower() == name.lower():
                return climate.climate_ref

    def event_exist(self, name):
        for event in self.thermostat_events:
            if event.name.lower() == name.lower():
                return True
        return False

    def set_thermostat_schedule(self, program, update=False, notify=False):
        title = message = None
        schedule = self.thermostat_schedule

        # prefill nested list with default climateRef (sleep)
        if schedule is None:
            schedule = []
            for i in range(7):
                schedule.append([])
                schedule[i].extend([self.DEFAULT_CLIMATE] * 48)

        # check if program is empty
        if not any(program):
            # No program changes required
            logger.info('No program updates, no changes made to the schedule.')
            return

        for idx, day in enumerate(program):
            if len(day) == 0:
                continue

            logger.debug(f'Setting the schedule for {helpers.get_day_name(idx)}.')

            last_time = '00:00'
            for climate_slot in day:
                climate_ref = climate_slot[0]

                # For setting prior nights sleep climate
                if len(climate_slot[2]) > 1:
                    if len(day) == 1:
                        last_time = climate_slot[2]
                        end_time = '23:30'
                    else:
                        end_time = climate_slot[2]
                else:
                    end_time = '23:30'
                slot_time_start, slot_time_end = helpers.get_time_slot(last_time, end_time)
                if slot_time_end == 47:
                    # Adjust for last slot of the day
                    slot_time_end += 1
                # for day_slot in slot_days:
                for slot in range(slot_time_start, slot_time_end):
                    schedule[idx][slot] = climate_ref
                    # temp_schedule[day_slot][slot] = climate
                last_time = end_time

        if update:
            logger.info('Attempting to update the thermostat schedule.')
            return_value = self.update_thermostat()
            if return_value > 0:
                # Success
                title = 'Ecobee schedule (Success)'
                message = 'Successfully updated thermostat schedule.'
                # ToDo: Add more robust logging on what the schedule was updated to
                #  Use 'program' variable with a climates name lookup by climateRef
                logger.info(message)
            elif return_value == 0:
                # No schedule changes required
                logger.info('No changes made to the schedule.')
            else:
                # Failure
                title = 'Ecobee schedule (Error)'
                message = f'Failure updating thermostat schedule --- {return_value}.'
                logger.error(message)

            if notify and title is not None:
                helpers.send_notifications(title, message)

    def days_to_set_are_all_timeofuse(self):
        # Verify that all the days requested to be updated in the schedule fall within time of use days
        if all(item in self.timeofuse_days for item in self.days_to_set):
            # All days to set fall on time of use days
            return True
        else:
            # At least one day to set falls on a day that is not time of use
            return False

    def days_to_set_are_partial_timeofuse(self):
        # Verify that any of the days requested to be updated in the schedule fall within time of use days
        if any(item in self.timeofuse_days for item in self.days_to_set):
            # At least one day to set falls on a time of use day
            return True
        else:
            # No days to set fall on a time of use day
            return False

    def thermostat_update_required(self):
        if not self.days_to_set_are_all_timeofuse():
            if self.timeofuse_restricted:
                logger.info('One or more days to set falls outside the time of use day range.\n'
                            'This is normal behavior but can be overridden by setting timeofuse_restricted '
                            'to \'False\' which will allow thermostat update.')
                return False
            else:
                logger.warning('One or more days to set falls outside the time of use day range.\n'
                               'timeofuse_restricted is set to \'False\', allowing thermostat update.')

        thermostat_response_temp = self.get_thermostats(self.selection)
        thermostat_schedule_temp = thermostat_response_temp[self.thermostat_index].program.schedule
        thermostat_climates_temp = thermostat_response_temp[self.thermostat_index].program.climates

        if thermostat_schedule_temp == self.thermostat_schedule:
            logger.debug('The schedule is already up to date, checking climates.')
            if len(helpers.compare_nested_structures(thermostat_climates_temp, self.thermostat_climates)) == 0:
                # No updates necessary
                logger.debug('The climates are already already up to date, no changes necessary.')
                return False

        return True

    def update_thermostat(self, force=False):
        if not force and not self.thermostat_update_required():
            return 0

        logger.info('Updating thermostats...')
        update_thermostat_response = self.ecobee_service.update_thermostats(
            selection=self.selection,
            thermostat=Thermostat(identifier=self.thermostat_identifier, program=Program(
                schedule=self.thermostat_schedule, climates=self.thermostat_climates)))

        if update_thermostat_response.status.code == 0:
            # After update a sleep is required for ecobee API to process the request
            time.sleep(10)

            # Update the thermostat object
            self.thermostat_list = self.selection

            logger.info('Successfully updated thermostats.')
            logger.info(update_thermostat_response.pretty_format())
            return 1
        else:
            logger.error(f'Failure while executing update_thermostats:\n{update_thermostat_response.pretty_format()}')
            return -1

    def set_new_climate_names(self, create=False, notify=False):
        # ToDo: Modify to not create the entire climate set, just create what
        #  is needed to set the days_to_set program values.
        self.new_climate_names = [f'{climate_name_prefix}{i}' for climate_name_prefix in
                                  self.new_climate_prefixes for i in range(7)]

        if create:
            return_value = self.create_new_climates()
            if return_value > 0:
                # Success
                if notify:
                    helpers.send_notifications('Ecobee Climate Creation (Success)',
                                               'Successfully created all new thermostat climates.')
                else:
                    logger.info('Successfully created all new thermostat climates.')
            elif return_value < 0:
                # Failure
                if notify:
                    helpers.send_notifications('Ecobee Climate Creation (Failure)',
                                               'Failure creating thermostat climates.')
                else:
                    logger.error('Failure creating thermostat climates.')
            else:
                # No climates created
                logger.info('All climates already exist, nothing to create.')

    def set_thermostat_climates(self, program, update=False, notify=False):
        title = message = None
        climates = self.thermostat_climates

        # check if program is empty
        if not any(program):
            # No program changes required
            logger.info('No program updates, no changes made to the climates.')
            return

        for idx, day in enumerate(program):
            if len(day) == 0:
                continue

            logger.debug(f'Setting climates for {helpers.get_day_name(idx)}.')

            for climate_slot in day:
                climate_ref = climate_slot[0]
                climate_temp = climate_slot[1]
                for climate in climates:
                    if climate.climate_ref.lower() == climate_ref.lower():
                        if climate_temp > 0:
                            climate.cool_temp = climate_temp

        if update:
            logger.info('Attempting to update thermostat climates.')
            return_value = self.update_thermostat()
            if return_value > 0:
                # Success
                title = 'Ecobee climates (Success)'
                message = 'Successfully updated thermostat climates.'
                # ToDo: Add more robust logging on what the climates were updated to
                #  Use 'program' variable with a climates name lookup by climateRef
                #  Restrict logging to sleep, precool, supercool climates (if necessary)
                logger.info(message)
            elif return_value == 0:
                # No schedule changes required
                logger.info('No changes made to the climates.')
            else:
                # Failure
                title = 'Ecobee climates (Error)'
                message = f'Failure updating thermostat climates --- {return_value}.'
                logger.error(message)

            if notify and title is not None:
                helpers.send_notifications(title, message)

    def get_program_values(self, notify=False):
        outdoor_temp_high = self.temp_high
        logger.info(f'Tomorrow\'s outdoor high temperature will be {str(outdoor_temp_high)[0:-1]}.'
                    f'{str(outdoor_temp_high)[-1]}{chr(176)}.')

        # Create empty program
        program = []
        for i in range(7):
            program.append([])

        # Validate supercool values
        if not isinstance(self.supercool_values, dict):
            logger.error('This function needs a dictionary of supercool program values.')
            return program

        # Climates should exist prior to calling this or climateRef won't be there yet
        if self.new_climate_names is None:
            logger.error('This function should be used after new climates exist, '
                         'please run set_new_climate_names() first.')
            return program

        # Validate hvac mode
        # if self.hvac_mode == "off":
        #     logger.info('The HVAC mode is OFF, nothing to do.')
        #     return program

        # Validate supercool months
        if not self.during_supercool_months:
            logger.info('Running outside supercool months, nothing to do.')
            return program

        # Supercool temp cutoff check
        if self.supercool_cutoff > outdoor_temp_high:
            # ToDo: Should something overwrite the schedule or leave this manual intervention?
            #  If no action is taken this leaves the supercool schedule in place
            #  Can a vacation be leveraged during on-peak hours for that day?
            title = 'Supercool cutoff not met'
            message = f'Supercool minimum outdoor temperature cutoff not met.\n' \
                      f'The outdoor temperature must be greater than ' \
                      f'{helpers.int_to_degreestring(self.supercool_cutoff)}{chr(176)}.'

            if self.days_to_set_are_partial_timeofuse():
                message = f'{message}\n\nThis will require manual intervention to prevent' \
                          f' the current schedule from running on a day that doesn\'t' \
                          f' need supercooling!\n'

                if notify:
                    helpers.send_notifications(title, message)

            logger.info(message)

            return program
        else:
            # Supercool temp threshold met, check if HVAC mode is off
            if self.hvac_mode == "off":
                title = 'Warning - HVAC mode is OFF'
                message = f'Supercool minimum outdoor temperature cutoff has been met.  ' \
                          f'However, the HVAC mode is off.\n\nThe HVAC mode will need to ' \
                          f'be turned ON manually prior to the precool schedule start ' \
                          f'time tomorrow.'

                logger.info(message)

                if notify:
                    helpers.send_notifications(title, message)

        for daynum in self.days_to_set:
            # Check if we have high temp for this day
            if self.high_temp_list[daynum] is None:
                logger.warning(f'There is no high temperature for {helpers.get_day_name(daynum)}, '
                               f'skipping setting this day.')
                continue

            # Handle setting prior nights sleep climate (only gets set if 'tomorrow' for day value)
            if daynum - 1 >= 0:
                previous_daynum = daynum - 1
            else:
                previous_daynum = 6
            climate_ref_previous = self.get_climate_ref(name=f'{self.new_climate_prefixes[-1]}{previous_daynum}')

            # Loop through supercool program values
            for sc_temp in self.supercool_values.keys():
                temp_list = helpers.get_range_from_string(sc_temp)
                if temp_list[0] <= outdoor_temp_high <= temp_list[1]:
                    for idx, slot in enumerate(self.supercool_values[sc_temp]):
                        climate_ref = self.get_climate_ref(name=f'{self.new_climate_prefixes[idx]}{daynum}')

                        program[daynum].append([climate_ref, slot[0], slot[1]])

                    # Set previous sleep night to match the mornings sleep temp
                    # ToDo: Modify this to work with any day, not just tomorrow
                    #  Will require pulling outdoor temp on a per day basis
                    if daynum == self.tomorrow_daynum:
                        program[previous_daynum] = [[climate_ref_previous,
                                                     self.supercool_values[sc_temp][0][0],
                                                     self.supercool_values[sc_temp][-2][1]]]

                    # Handle last day of time of use
                    if daynum == self.timeofuse_days[-1]:
                        logger.info('Last day of time of use detected, override sleep temp.')
                        program[daynum][-1] = [self.get_climate_ref(name=f'{self.new_climate_prefixes[-1]}{daynum}'),
                                               self.supercool_values[sc_temp][-2][0],
                                               ""]

        if not any(program):
            logger.error('No program values returned, exiting')
            exit()

        logger.info('Supercool program values retrieved.')
        return program

    def add_thermostat_climate(self, name):
        # ToDo: Have this pull a list of sensors instead of cloning an existing climates sensors
        #  There are challenges when trying to do this.  Compare default_sensors to self._thermostat_sensors
        default_sensors = self.thermostat_climates[0].sensors
        self.thermostat_climates.append(Climate(name=name,
                                                is_occupied=True,
                                                is_optimized=True,
                                                cool_fan='auto',
                                                heat_fan='auto',
                                                owner='user',
                                                ventilator_min_on_time=20,
                                                sensors=default_sensors
                                                )
                                        )

    def create_new_climates(self):
        if self.new_climate_names is None:
            logger.warning('No new climate names found, returning.')
            return

        climates_created = []
        climates_exist = []

        for climate in self.new_climate_names:
            successful = False
            while not successful:
                duplicate = False
                if self.get_climate_ref(name=climate) is None:
                    # Climate missing, add it
                    self.add_thermostat_climate(name=climate)

                    # Update the thermostat with new climate
                    # Note: Ecobee API only lets you add a single climate per API call
                    self.update_thermostat(force=True)

                    # check no duplicate climateRef properties exist (ecobee API serialization error)
                    for idx, temp_climate in enumerate(self.thermostat_climates):
                        if idx + 1 < len(self.thermostat_climates) and idx - 1 >= 0:
                            if temp_climate.climate_ref == self.thermostat_climates[idx - 1].climate_ref or \
                                    temp_climate.climate_ref == self.thermostat_climates[idx - 2].climate_ref:
                                logger.warning(f'Duplicate climateRef found: {temp_climate.name}')
                                # ToDo: Need to determine a proper fix, the climate will need to be recreated
                                duplicate = True
                                break

                    # duplicate found, repeat loop
                    if duplicate:
                        logger.debug(f'Duplicate climateRef found for climate {climate}, '
                                     f'repeating climate creation loop')
                        continue

                    # no duplicate climateRef found
                    logger.info(f'Successfully created climate: {climate}')
                    climates_created.append(climate)
                    successful = True
                else:
                    # climate already exists
                    logger.debug(f'Climate already exists: {climate}')
                    climates_exist.append(climate)
                    successful = True

        if len(climates_exist) + len(climates_created) == len(self.new_climate_names):
            # Success
            return len(climates_created)
        else:
            # Failure
            return -1

    def create_vacation(self, name, start_date, end_date, cool_temp, heat_temp=45, force=False):
        if not self.timezone:
            logger.error('No time zone, set your timezone on the ecobee website')
            return False

        tz = timezone(self.timezone)
        # Subtract a day from off-peak (vacation) start date to handle the previous nights sleep climate override
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M") - timedelta(days=1)
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")

        # Check if end_date is in the past
        if end_date < datetime.today():
            logger.info(f'Off-peak vacation "{name}" occurs in the past, skipping creation')
            return False

        # Check if event (vacation) already exists
        if self.event_exist(name) and force:
            logger.info(f'Off-peak vacation "{name}" already exists, deleting existing vacation')
            # Delete the vacation
            if not self.delete_vacation(name=name):
                logger.warning(f'Unable to delete off-peak vacation "{name}"')
                return False
        elif self.event_exist(name):
            logger.info(f'Off-peak vacation "{name}" already exists')
            return False

        logger.info(f'Creating off-peak vacation "{name}"')
        update_thermostat_response = self.ecobee_service.create_vacation(
            name=name,
            cool_hold_temp=cool_temp,
            heat_hold_temp=heat_temp,
            start_date_time=tz.localize(start_date,
                                        is_dst=self.isdaylightsavings),
            end_date_time=tz.localize(end_date,
                                      is_dst=self.isdaylightsavings),
            fan_mode=FanMode.AUTO,
            fan_min_on_time=0)

        if update_thermostat_response.status.code == 0:
            # After update a sleep is required for ecobee API to process the request
            time.sleep(10)

            # Update the thermostat object
            self.thermostat_list = self.selection

            logger.info('Successfully created off-peak vacation(s)')
            logger.info(update_thermostat_response.pretty_format())
            return True
        else:
            logger.error(f'Failure creating off-peak vacation:\n{update_thermostat_response.pretty_format()}')
            return False

    def delete_vacation(self, name):
        if not self.event_exist(name):
            logger.info(f'Off-peak vacation "{name}" does not exist, nothing to do')
            return True

        logger.info(f'Deleting off-peak vacation "{name}"')
        update_thermostat_response = self.ecobee_service.delete_vacation(name=name)

        if update_thermostat_response.status.code == 0:
            # After update a sleep is required for ecobee API to process the request
            time.sleep(10)

            # Update the thermostat object
            self.thermostat_list = self.selection

            logger.info('Successfully deleted off-peak vacation.')
            logger.info(update_thermostat_response.pretty_format())
            return True
        else:
            logger.error(f'Failure deleting off-peak vacation:\n{update_thermostat_response.pretty_format()}')
            return False
