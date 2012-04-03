# This file's extension says .ini indicating it is a config file, but it's
# really a python source file containing the configuration for fedmsg.

config = dict(
    io_threads=1,

    endpoints="tcp://*:6543,tcp://*:5432",

    relay="tcp://127.0.0.1:2003",

    # Default is 0
    high_water_mark=1,

    # Set this to dev if you're hacking on fedmsg or an app.
    # Set to stg or prod if running in the Fedora Infrastructure
    environment="dev",
)
