# ESB Networks Smart Meter Data to InfluxDB
![](https://github.com/badger707/esb-smart-meter-reading-automation/blob/main/esb-smart-meter.png)

I've wanted to get the ESB smart data into my [Home Assistant](https://www.home-assistant.io/) setup ever since the energy dashboard became available. Since the meter reports the kW consumed every 30 mins, you'd think an API would be obvious for the end-users, but apparently not.

Thanks to work by [badger707](https://github.com/badger707/esb-smart-meter-reading-automation) and [others](#references) we have a fairly good screen-scraping solution, so this fork is just to clean it up a bit, and document the integration to Home Assistant.

NOTES:
* You need to create account with ESB here https://myaccount.esbnetworks.ie 
* In your account, link your electricity meter MPRN

# Notes on the source data
* The call to the ESB portal allows the period to be specified, and the script provides today as the date requested. Unfortunately, this parameter is ignored, so we get *all* the records available e.g. 20k+ and counting.
* The data is provided every 30 mins in kW units. Home assistant requries this in *kWh* so in the sensor definition I multiple the value by 0.5 to adjust.
* The timestamp in the source data is in Irish Standard Time, so I convert to UNIX EPOCH before inserting into the database.

# Script usage

The script will run on demand, or via cron. The required parameters should be in a `.secrets` file, in the same directory as the script. This is written in python3, and the `requirements.txt` file shows the dependancies.

It works off of *all* the data retrieved, so will become less efficient as time goes on. If there is a matching timestamp already in the database, it will be updated with the new value, otherwise any missing data will be inserted.

The following are the required parameters for the config file.
## Config file format

```ini
[influx]
HOST=<influx db server hostname/IP> 
USER=<username>
PASSWORD=<password>
DB=<name of database>

[esb]
USER=<email address registered with ESB Networks>
PASSWORD=<password>
MPRN=<MPRN - meter reference number, on your bill>
```

# Home Assistant Sensor Configuration

This is in my `sensors.yaml`
```yaml

  - platform: influxdb
    api_version: 1
    host: <host>
    username: <username>
    password: <password>
    database: <database>
    verify_ssl: false
    ssl: false
    queries:
      - name: ESB Power
        unit_of_measurement: kWh
        value_template: "{{ value | multiply(0.5) }}"
        group_function: last
        measurement: '"meter_reading"'
        field: value
        where: '"MPRN" = ''<MPRN>'''
```
but we also need to adjust `customize.yaml` to ensure that we set the type correctly
```yaml
---
customize:
  sensor.esb_power:
    device_class: energy
    state_class: total

```
# Change Notes
* Tested 03/01/2024 - working

# References
* [https://www.boards.ie/discussion/2058292506/esb-smart-meter-data-script](https://www.boards.ie/discussion/2058292506/esb-smart-meter-data-script)
* [https://gist.github.com/schlan/f72d823dd5c1c1d19dfd784eb392dded](https://gist.github.com/schlan/f72d823dd5c1c1d19dfd784eb392dded)
* [https://github.com/badger707/esb-smart-meter-reading-automation](https://github.com/badger707/esb-smart-meter-reading-automation)