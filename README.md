# HAN Power meter

A Python3 script to read, save and publish via MQTT the power meter data.

This script will use the power meter Home Area Network - HAN port to read data
from the power meter. While it has been tested on a Kaifa model MA 109P, it may
work with all other makes in the Portuguese model as well.

The script has been tested on an ASUS Tinker board running Linaro OS with a
USB RS485 adapter.

The script will collect the counters values, save them in a local csv file
and publish them via MQTT to a topic you may define. The collected counters
are:

 year       imported vazio    exported vazio  	imported total
 month      imported cheia    exported cheia    exported total
 day        imported ponta    exported ponta    voltage
 minutes

Please notice that this is for the Portuguese standards. The registers to get
the counters data are defined at EDP Distribuição document DEF-C44-509.pdf.

It is expected that cron will be used to run this program every 15 minutes.
To do so, include it on the system /etc/crontab file:

7  * * * *       root    /usr/bin/python3 /home/linaro/load_logger.py
22 * * * *       root    /usr/bin/python3 /home/linaro/load_logger.py
37 * * * *       root    /usr/bin/python3 /home/linaro/load_logger.py
52 * * * *       root    /usr/bin/python3 /home/linaro/load_logger.py

Before using, make sure you set the file location and MQTT credentials to match
your system.
