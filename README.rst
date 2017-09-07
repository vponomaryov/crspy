========================================================
Currency exchange rates in bank Basis (Ukraine, Kharkov)
========================================================

'crspy' stands for "Currency Rates SPY", it consists of data collector and
image builder.
It loads main page of 'kurs.kharkov.com' site and then parses it to get
current currency exchange rates.
Then it puts parsed data to files as serialized json as of following format:

/path/to/this/project/data/year_%year%/month_%month%/%Y_%m_%d__%H_%M_%S.json

It is recommended to run collector periodically using
any kind of scheduler like 'cron'.

Dependencies
------------

System dependencies:
    * firefox<47.0.0     # (collector, tested with firefox==40.0.0)
    * xvfb               # (collector)
    * python>=3.0

Python dependencies:
    * selenium==2.53.1   # (collector)
    * pyvirtualdisplay   # (collector)
    * matplotlib>=2.0.2  # (image builder)

Usage
-----

To collect current data use following command:

    $ python3 -m crspy.collector

To test collector not writing data to files run following:

    $ python3 -m crspy.collector test

To specify custom path to FireFox binary run following:

    $ python3 -m crspy.collector bin=/path/to/firefox/binary

To build images from collected data run following:

    $ python3 -m crspy.img_builder

It creates images with graphs per each month of each available year
and puts it them to 'data/year_%year%' dirs.
