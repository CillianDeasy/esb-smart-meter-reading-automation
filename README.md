# ESB Networks Smart Meter Data to InfluxDB





# Config file format

```
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



![](https://github.com/badger707/esb-smart-meter-reading-automation/blob/main/esb-smart-meter.png)
<br><br>
# How to read your Smart Meter data automatically?
<br>
Since I've got smart meter installed, I was looking for a way to automatically collect my meter data to track electricity usage (and solar export) with corresponding pricing as per current supplier rates.<br><br>
While searching on internet I found this post https://www.boards.ie/discussion/2058292506/esb-smart-meter-data-script as potential candidate to start with.
<br>
Unfortunatelly linked script is broken - ESB have chnaged some URL's and file structure since then and I had to spend some time and tinker with code to make it working with new (as of writing it is 21-JUL-2023) URL structure.<br><br>
End result - code is fixed and runs just fine now, I am able to read all smart meter readings from my account in JSON format and push it further to my InfluxDB and Home Assistant for analysis/reporting.
<br><br>
# Requirements<br>
* You need to create account with ESB here https://myaccount.esbnetworks.ie <br>
* In your account, link your electricity meter MPRN
<br><br>
# Script setup<br>
* In script - update MPRN, user and password at the bottom of the code

<br><br>
I hope this will be usefull, cheers!
<br><br>
```



# References
* [](https://www.boards.ie/discussion/2058292506/esb-smart-meter-data-script)
* [](https://gist.github.com/schlan/f72d823dd5c1c1d19dfd784eb392dded)
* [](https://github.com/badger707/esb-smart-meter-reading-automation)