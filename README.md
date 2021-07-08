# pyecobee-supercool

This repository allows for setting a dynamic supercool schedule using the Ecobee API in Python programs.
The cool temperature and schedule for the climates are adjusted based on the outdoor temperature.

This repository leverages the pyecobee python library located [here](https://github.com/sfanous/Pyecobee).

See additional documentation on the Ecobee API 
[here](https://www.ecobee.com/home/developer/api/introduction/index.shtml).

## Supercool Information
This program is best for those on a time-of-use plan from your utility company.
Certain days of the week will have off-peak and on-peak hours.
Supercooling consists of precooling your house during off-peak (less expensive) hours and not running the AC at all
during the on-peak hours.

A typical days schedule for supercooling consists of the following climates (in this order):
- Sleep
- Precool
- Supercool
- Time of Use/On-peak (Away)
- Home
- Sleepnight

### Supercool Gauge
The amount of supercooling necessary is dependent on many factors such as:
- Outside temperature
- House square footage
- Single or double story
- Which way the house faces
- How many AC units you have
- How efficient your house is (insulation, windows, doors, etc.)
- How many hours of on-peak there are each time-of-use day

The main takeaway there is that you <ins>don't</ins> need to supercool your house to the same level if the outside
high temp will be 90° versus when it's 110° outside.

The below table is just an example.  It is based on a 5-hour on-peak time window.

|Outdoor Temp|Sleep Temp|Precool Start|Precool Temp|Supercool Start|Supercool Temp|
|------------|:--------:|:-----------:|:----------:|:-------------:|:------------:|
|88° - 97°   |76°       |12:30        |75°         |13:30          |74°           |
|98° - 102°  |76°       |12:00        |75°         |12:30          |73°           |
|103° - 105° |75°       |11:30        |74°         |12:30          |72°           |
|106° - 108° |75°       |10:30        |73°         |12:00          |71°           |
|109° - 111° |74°       |10:00        |72°         |11:30          |70°           |
|112° - 114° |74°       |09:00        |71°         |11:00          |69°           |
|115° - ?    |73°       |08:00        |70°         |11:00          |68°           |

**Note:**
- The table is based on on-peak time between: 15:00 - 20:00
- Your start times and cool temps will vary.
- The supercool temps in the table require that the target cool temp is reached prior to on-peak, 
  15:00 in this example. This may require starting the precool and supercool climates earlier in
  the day and/or lowering the cool temps for the climates leading up to on-peak.

## Initial set up
Clone/download the repository and run `pip install -r requirements.txt`.

### Logging In

```python
from ecobee import core
ecobee_service = core.authenticate("Home") 
```

See main.py for additional example usage.
Main.py configuration values are stored in the `local_settings.py` file.
To create the `local_settings.py` file initially just use the `sample_local_settings.py` file as a template.

## Documentation

### Program (Climates and Schedule)
Update the `supercool_values` variable in the `local_settings.py` file based on your own Supercool gauge for 
your house.  This value is a dictionary with nested lists.  The temperatures are padded so for example, 1089 is 108.9°.
The climate names and order used in `supercool_values` are based on the `climates` variable in `local_settings.py`.

I've taken the liberty of showing the `supercool_values` in a table layout for a better visualization of what 
`supercool_values` represents.

|Outdoor Temp Range  |Sleep Temp|Sleep End Time|Precool Temp|Precool End Time|Supercool Temp|Supercool End Time|Away Temp|Away End Time|Home Temp|Home End Time|Home Temp|Sleepnight End Time|
|--------------------|:--------:|:------------:|:----------:|:--------------:|:------------:|:----------------:|:-------:|:-----------:|:-------:|:-----------:|:-------:|:-----------------:|
|"880-979"           |760       |"12:30"       |750         |"13:30"         |740           |"15:00"           |820      |"20:00"      |770      |"22:00"      |760      |""                 |
|"980-1029"          |760       |"12:00"       |750         |"12:30"         |730           |"15:00"           |820      |"20:00"      |770      |"22:00"      |760      |""                 |
|"1030-1059"         |750       |"11:30"       |740         |"12:30"         |720           |"15:00"           |820      |"20:00"      |770      |"22:00"      |750      |""                 |
|"1060-1089"         |750       |"10:30"       |730         |"12:00"         |710           |"15:00"           |820      |"20:00"      |770      |"22:00"      |750      |""                 |
|"1090-1119"         |740       |"10:00"       |720         |"11:30"         |700           |"15:00"           |820      |"20:00"      |770      |"22:00"      |740      |""                 |
|"1120-1149"         |740       |"09:00"       |710         |"11:00"         |690           |"15:00"           |820      |"20:00"      |770      |"22:00"      |740      |""                 |
|"1150-1300"         |730       |"08:00"       |700         |"11:00"         |680           |"15:00"           |820      |"20:00"      |770      |"22:00"      |730      |""                 |

A few things to note:
- Start times of each climate are omitted.
    - As such the first climate of each day (sleep) starts at 00:00.
    - The last climate of each day (sleepnight) goes until 23:30 (last schedule slot of the day).  
      This is why the last climate end times are empty quotes.

One challenge with this dynamic approach to climates is that they will step on each other.  One example is if you
use the `Sleep` climate in the morning and again at night on the same day.  In this scenario you can't have
unique climate values for morning sleep versus night sleep.  To workaround the issue of
overwriting climates still remaining on the current day, each day has a unique set of climates.
- Monday: sleep0, precool0, supercool0, away0, home0, sleepnight0
- Tuesday: sleep1, precool1, supercool1, away1, home1, sleepnight1
- Wednesday: sleep2, precool2, supercool2, away2, home2, sleepnight2
- Etc.

**Note:** For this design to work the built-in (system) climates are no longer used.

### Off-peak Holidays
Some utilities observe certain holidays as off-peak days for time-of-use plans.
To allow for this, Ecobee vacations are used on off-peak days in order to allow for a static cool temp.
This essentially bypasses what would normally be a supercool day.

#### Notes:
- Off-peak vacations will only be created if the `timeofuse_holidays` date is in the future.
- By default, if the off-peak vacation already exists it will not overwrite.
  - There is a force=True parameter on the create_vacation() function that will delete the existing off-peak
    vacation and recreate.
- Vacations don't pad the temperature like other areas of the Ecobee API.  So 77° is 77 and not 770.

#### Example
To set the off-peak days edit the `timeofuse_holidays` values in the local_settings.py with comma separated dates
```python
timeofuse_holidays = "2021-07-05,2021-09-06"
timeofuse_holidays_cool_temp = 77
timeofuse_holidays_start_time = "20:00"
timeofuse_holidays_end_time = "20:00"
```
With the above configuration two vacations will be created. The first is created from 2021-07-04 20:00 to 
2021-07-05 20:00 with a cool temp set to 77 during the vacation. Notice that the start date is actually the 
day before (07-04) in order to override the last climate of the previous day (sleepnight).

### local_settings.py
- **logfile:** Log file path
- **loglevel:** Log level
- **thermostat_name:** Name of the Ecobee thermostat
- **climates:** List of climates name prefixes in order (comma seperated)
- **supercool_values:** Dictionary with nested lists reflecting the supercool program values (see Program section above) 
- **days_to_set:** The days you want to set the program for. (comma separated)
  - Allows for varied values like "Mon,Tue,Wednesday" or "tomorrow" or "weekdays" for example. 
- **timeofuse_day_range:** A day range reflecting time-of-use days.  This is expected to be a consecutive day range.
  - This is a day index starting with 0 - Monday.  So `"0-4"` would be Monday-Friday as your time-of-use days.
- **timeofuse_restricted:** Whether or not to limit the days being set to time-of-use days. (bool)
  - If `True` and the `days_to_set` fall outside a time-of-use day then no change is made.
- **timeofuse_holidays:** A list of off-peak vacation days. (comma separated)
- **timeofuse_holidays_cool_temp:** The cool temp to hold the program at during the off-peak vacation days. (not padded)
- **timeofuse_holidays_start_time:** The start time for the off-peak vacation days.
  - Since the off-peak vacation days start the day prior this should typically be "20:00" or "22:00" 
    (i.e. the start of sleepnight climate from previous day) (see Off-peak Holidays section above)
- **timeofuse_holidays_end_time:** The end time for the off-peak vacation days.
  - This should end when the sleepnight climate begins, typically "20:00" or "22:00".
- **supercool_low_temp_cutoff:** The low-end cutoff temperature to decide whether this program will make any changes.
  - For example, if the cutoff is set to 879 (87.9°) but the outside temperature will only reach 865 (86.5°).
    No changes will be made to the climates or schedule for that day.

See example file `sample_local_settings.py` for reference.

### Notifications
The program supports the following notification services:
- Pushbullet
- Join (joaoapps)
- Pushover
- Email

Each can be configured with relative ease in the `local_settings.py` file.

## Assumptions and Limitations
- Time-of-use days are consecutive.  For example, Monday-Friday (0-4).
- Currently, using the Ecobee API weather forecast data (for outdoor temp) which is limited to 4 days.
- Leverages new (unique) climates for each day of the week.
- The built-in (system) climates are no longer used.
- This does not delete any climates.
- This does not create climates for days with no on-peak hours (by default) like weekends for example.
  One option is to use a static `Weekend` climate set to a specific cool temp like 77° to cover Saturday and Sunday.
- eco+ mode is disabled indefinitely.
- Currently, only works with a single thermostat.
- Time of use (off-peak) holidays will need to be updated each year in `local_settings.py`.

## Bugs and Contributing

Please feel free to report issues or make general improvements by 
[raising a new issue](https://github.com/permster/pyecobee-supercool/issues/new) and/or 
[open a pull request](https://github.com/permster/pyecobee-supercool/compare).
