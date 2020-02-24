# vrops-exporter
Prometheus exporter to scrape metrics from vRealize Operations Manager

## Running the exporter

The container is defaulting to /vrops-exporter path. Use vrops-exporter.py with one of the two ways of specifying the necessary credentials. They could also be mixed of course.

1. CLI

```
Usage: vrops-exporter.py [options]
```
Options:

short | long | description
--- | --- | ---
  -h | --help |           show this help message and exit
  -u USER | --user=USER | specify user to log in
  -p PASSWORD | --password=PASSWORD | specify password to log in
  -o PORT | --port=PORT | specify exporter port
  -a CONFIGFILE | --atlas | specify atlas configfile 
  -d | --debug    |       enable debug


2. Enviroment variables

```
USER
PASSWORD
PORT
```

## Service discovery way of querying
Query with: ``http://localhost:CONTAINERPORT``


## Testing
Test module is called using ENV variables. Specifying these on the fly would look like this:

```
DEBUG=0 USER=foo PASSWORD=bar python3 tests/TestCollectors.py
```

Please note, that USER and PW don't do anything at all currently, they are just being passed because VropsCollector.py is checking that these are present.

## Resources
![Class Diagram](https://yuml.me/032071b0.png)
