#!/bin/bash
echo "alias python=python3" >> ~/.bashrc 
echo "alias pip=pip3" >> ~/.bashrc 
source ~/.bashrc
service postgresql start
apt update && apt upgrade -y
apt install python3-pip -y
apt-get install python-psycopg2 -y
apt-get install libpq-dev -y
python3 -m pip install -r code/requirements.txt
createdb blockchain
python3 code/database/setup.py
gunicorn -b 0.0.0.0:5000 --workers=1 --chdir /code/ node:app