# Power meter logger using HAN

This program will use the power meter Home Area Network - HAN port to read data
from the power meter, save it on a local file while also publish it via MQTT.

While it has been tested on a Kaifa model MA 109P power meter, it may work with
all other makes used in the Portugal. To use it in another country you may need
to change the registers addresses it uses to collect data.

The script has been tested on an ASUS Tinker board running Linaro OS with a
USB RS485 adapter.

The collected counters are:
```
 year       imported vazio    exported vazio   imported total
 month      imported cheia    exported cheia   exported total
 day        imported ponta    exported ponta   voltage
 minutes
```
Please notice that this is for the Portuguese standards. The registers to get
the counters data are defined at EDP Distribuição document DEF-C44-509.pdf.

It is expected that cron will be used to run this program every 15 minutes.
To do so, include the script on the system /etc/crontab file:

```
7  * * * *  root  /usr/bin/python3 /home/linaro/power_logger.py
22 * * * *  root  /usr/bin/python3 /home/linaro/power_logger.py
37 * * * *  root  /usr/bin/python3 /home/linaro/power_logger.py
52 * * * *  root  /usr/bin/python3 /home/linaro/power_logger.py
```
Before using it, make sure you set the file location and MQTT credentials to
match your system.

Dependencies: python3 and python modules crcmod and paho.
