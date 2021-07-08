# pyecobee-supercool

This repository allows for setting a dynamic supercool schedule using the Ecobee API in Python programs.
The cool temperature and schedule for the climates are adjusted based on the outdoor temperature.

This repository leverages the pyecobee python library located [here](https://github.com/sfanous/Pyecobee)

See additional documentation on the Ecobee API [here](https://www.ecobee.com/home/developer/api/introduction/index.shtml).

## Supercool Information
This program is best for those on a time-of-use plan from your utility company.
Certain days of the week will have off-peak and on-peak hours.
Supercooling consists of precooling your house during off-peak (less expensive) hours.

A typical days schedule for supercooling consists of the following climates (in this order):
- Sleep
- Precool
- Supercool
- Time of Use (Away)
- Home
- Sleepnight

###Supercool Gauge
The below table is just an example.  Your start times and cool temps will vary depending on many factors such as:
- House square footage
- Single or double story
- Which way the house faces
- How many AC units you have
- How efficient your house is (insulation, windows, doors, etc.)
- How many hours of on-peak there are each time-of-use day (table based on a 5-hour on-peak window)

**Table based on on-peak time between:** 15:00 - 20:00

|Outdoor Temp|Sleep Temp|Precool Start|Precool Temp|Supercool Start|Supercool Temp|
|------------|:--------:|:-----------:|:----------:|:-------------:|:------------:|
|88° - 97°   |76°       |12:30        |75°         |13:30          |74°           |
|98° - 102°  |76°       |12:00        |75°         |12:30          |73°           |
|103° - 105° |75°       |11:30        |74°         |12:30          |72°           |
|106° - 108° |75°       |10:30        |73°         |12:00          |71°           |
|109° - 111° |74°       |10:00        |72°         |11:30          |70°           |
|112° - 114° |74°       |09:00        |71°         |11:00          |69°           |
|115° - ?    |73°       |08:00        |70°         |11:00          |68°           |

**Note:** The supercool temps in the table require that the target cool temp is reached prior to time of use, 15:00 in this example.
This may require starting the precool and supercool climates earlier in the day.

## Initial set up
Clone/download the repository and run `pip install -r requirements.txt`.

## Logging In

```python
from ecobee import core
ecobee_service = core.authenticate("Home") 
```

## Assumptions and Limitations
- Time-of-use days are consecutive.  For example, Monday-Friday (0-5).
- Currently, using the Ecobee API for weather forecast data (for outdoor temp) which is limited to 4 days.
- Leverages new (unique) climates for each day of the week.
- The built-in (system) climates are no longer used.
- This program does not delete any climates.
- This program does not create climates for days with no time-of-use like weekends for example.  One option is to use a static `Weekend` climate set to a specific cool temp like 77° to cover Saturday and Sunday.
- eco+ mode is disabled indefinitely

## Documentation

### Program (Climates and Schedule)
Update the program values under the get_program_values() function in core.py based on your own Supercool gauge for your house. 

To workaround the issue of overwriting climates still remaining on the current day each day has a unique set of climates.
- Monday: sleep0, precool0, supercool0, away0, home0, sleepnight0
- Tuesday: sleep1, precool1, supercool1, away1, home1, sleepnight1
- Wednesday: sleep2, precool2, supercool2, away2, home2, sleepnight2
- Etc.

Note: For this design to work the built-in (system) climates are no longer used.

### Off-peak Holidays
Some utilities observe certain holidays as off-peak days for time-of-use plans.
To allow for this, Ecobee vacations are used on off-peak days in order to allow for a static cool temp.
This essentially bypasses what would normally be a supercool day.

#### Example
To set the off-peak days edit the `timeofuse_holidays` values in the local_settings.py with comma separated dates
```python
timeofuse_holidays = "2021-07-05,2021-09-06"
timeofuse_holidays_cool_temp = 77
timeofuse_holidays_start_time = "20:00"
timeofuse_holidays_end_time = "20:00"
```
In the above example two vacations will be created.
The first is created from 2021-07-04 20:00 to 2021-07-05 20:00 with a cool temp set to 77 during the vacation.
Notice that the start date is actually the day before (07-04) in order to override the previous nights sleep climate.

See main.py for additional example usage.  Main.py configuration values are stored in local_settings.py.  See example file `sample_local_settings.py`.

## Bugs and Contributing

Please feel free to report issues or make general improvements by [raising a new issue](https://github.com/permster/pyecobee-supercool/issues/new) and/or [open a pull request](https://github.com/permster/pyecobee-supercool/compare).
