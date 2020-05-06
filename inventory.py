#!/usr/bin/python3
from InventoryBuilder import InventoryBuilder
from optparse import OptionParser
import sys
import os


def parse_params():
    parser = OptionParser()
    parser.add_option("-u", "--user", help="specify user to log in", action="store", dest="user")
    parser.add_option("-p", "--password", help="specify password to log in", action="store", dest="password")
    parser.add_option("-o", "--port", help="specify exporter port", action="store", dest="port")
    parser.add_option("-a", "--atlas", help="path to atlas configfile", action="store", dest="atlas")
    parser.add_option("-d", "--debug", help="enable debug", action="store_true", dest="debug", default=False)
    parser.add_option("-l", "--loopback", help="use 127.0.0.1 address instead of listen to 0.0.0.0",
                      action="store_true", dest="loopback")
    (options, args) = parser.parse_args()

    if options.user:
        os.environ['USER'] = options.user
    if options.password:
        os.environ['PASSWORD'] = options.password
    if options.debug:
        os.environ['DEBUG'] = "1"
        print('DEBUG enabled')
    else:
        if 'DEBUG' not in os.environ.keys():
            os.environ['DEBUG'] = "0"
        else:
            print('DEBUG enabled')
    if options.loopback:
        os.environ['LOOPBACK'] = "1"
    if options.port:
        os.environ['PORT'] = options.port
    if options.atlas:
        os.environ['ATLAS'] = options.atlas

    if "PORT" not in os.environ and not options.port:
        print("Can't start, please specify port with ENV or -o")
        sys.exit(0)
    if "USER" not in os.environ and not options.user:
        print("Can't start, please specify user with ENV or -u")
        sys.exit(0)
    if "PASSWORD" not in os.environ and not options.password:
        print("Can't start, please specify password with ENV or -p")
        sys.exit(0)
    if "ATLAS" not in os.environ and not options.atlas:
        print("Can't start, please specify atlas with ENV or -a")
        sys.exit(0)

    return options


if __name__ == '__main__':
    options = parse_params()
    InventoryBuilder(options.atlas, os.environ['PORT'])
