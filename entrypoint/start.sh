#!/bin/bash

service postgresql start
gunicorn -b 0.0.0.0:5000 --workers=5 --chdir /code/ node:app