logfile = "pyecobee-supercool.log"
loglevel = "WARNING"
thermostat_name = "Home"
climates = "sleep,precool,supercool,away,home,sleepnight"  # Order needs to match supercool_values order below
supercool_values = {
    "820-879": [[770, "12:30"], [770, "14:30"], [750, "16:00"], [820, "19:00"], [770, "22:00"], [770, ""]],
    "880-979": [[760, "12:30"], [750, "13:30"], [740, "16:00"], [820, "19:00"], [770, "22:00"], [760, ""]],
    "980-1029": [[760, "12:00"], [750, "12:30"], [730, "16:00"], [820, "19:00"], [770, "22:00"], [760, ""]],
    "1030-1059": [[750, "11:30"], [740, "12:30"], [720, "16:00"], [820, "19:00"], [770, "22:00"], [750, ""]],
    "1060-1089": [[750, "10:30"], [730, "12:00"], [710, "16:00"], [820, "19:00"], [770, "22:00"], [750, ""]],
    "1090-1119": [[740, "10:00"], [720, "11:30"], [700, "16:00"], [820, "19:00"], [770, "22:00"], [740, ""]],
    "1120-1149": [[740, "09:00"], [710, "11:00"], [690, "16:00"], [820, "19:00"], [770, "22:00"], [740, ""]],
    "1150-1300": [[730, "08:00"], [700, "11:00"], [680, "16:00"], [820, "19:00"], [770, "22:00"], [730, ""]]
}
days_to_set = "tomorrow"
timeofuse_day_range = "0-4"
timeofuse_restricted = True
timeofuse_holidays = "2023-01-01," \
                     "2023-01-16," \
                     "2023-02-20," \
                     "2023-03-31," \
                     "2023-05-29," \
                     "2023-07-04," \
                     "2023-09-04," \
                     "2023-11-10," \
                     "2023-11-23," \
                     "2023-12-25"
timeofuse_holidays_cool_temp = 77
timeofuse_holidays_start_time = "19:00"
timeofuse_holidays_end_time = "19:00"
supercool_low_temp_cutoff = 819
supercool_month_range = "04-10"
notifications_enabled = True
pushbullet_enabled = False
pushbullet_apikey = ""
pushbullet_deviceid = ""
join_enabled = False
join_apikey = ""
join_deviceid = ""
pushover_enabled = False
pushover_keys = ""
pushover_priority = ""
pushover_apitoken = ""
email_enabled = True
email_from = "test@gmail.com"
email_to = "janedoe@gmail.com,johndoe@gmail.com"
email_ssl = False
email_smtp_server = "smtp.gmail.com"
email_smtp_port = 587
email_tls = True
email_smtp_user = "test"
email_smtp_password = "<app password if using gmail>"
