# SLA Dashboard #

This is the README.txt file for sla-dashboard application.

sla-dashboard application is composed by the following directories:

* sladashboard: the app related to the application itself. The settings
    file maybe need to be modified: read below.
* slagui: the sla dashboard GUI project.
* slaclient: this project contains all the code needed to connect to
    SLA Manager REST interface, and the conversion from xml/json to python
    objects.
* samples: this directory contains sample files to load in the SLA Manager for
    testing.
* bin: some useful scripts


##Software requirements##

Python version: 2.7.x

The required python packages are listed in requirements.txt

Installing the requirements inside a virtualenv is recommended.

SLA Manager (java backend) needs to be running in order to use the dashboard.

##Installing##

    #
    # Install virtualenv
    #
    $ pip install virtualenv


    #
    # Create virtualenv.
    # E.g.: VIRTUALENVS_DIR=~/virtualenvs
    #
    $ virtualenv $VIRTUALENVS_DIR/sla-dashboard
    
    #
    # Activate virtualenv
    #
    $ . $VIRTUALENVS_DIR/sla-dashboard/bin/activate
    
    #
    # Change to application dir and install requirements
    #
    $ cd $SLA_DASHBOARD
    $ pip install -r requirements.txt
    
    #
    # Create needed tables for sessions, admin, etc
    #
    $ ./manage.py syncdb

##Settings##


* sladashboard/settings.py:
    - SLA_MANAGER_URL : The URL of the SLA Manager REST interface (defaults to http://localhost:9040)
    - DEBUG: Please, set this to FALSE in production (defaults to FALSE)

##Running##

NOTE: this steps are not suitable in production mode.

    #
    # Activate virtualenv
    #
    $ . $VIRTUALENVS_DIR/sla-dashboard/bin/activate
    
    #
    # Cd to application dir
    #
    $ cd $SLA_DASHBOARD
    
    #
    # Start server listing in port 8000 (change port as desired)
    #
    $ bin/runserver
    
    #
    # Test
    #
    curl http://localhost:8000
    
## License ##

Licensed under the [Apache License, Version 2.0][1]


[1]: http://www.apache.org/licenses/LICENSE-2.0
