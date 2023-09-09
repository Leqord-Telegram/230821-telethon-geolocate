#!/bin/bash

echo "User telebot-user should have been created! useradd -m -U telebot-user"

apt install postgresql postgresql-contrib
systemctl enable postgresql
systemctl start postgresql

sleep 15

sudo -i -u postgres psql -a -f "/telebot-server/230821-telethon-geolocate/sql/init.sql"
sudo -i -u postgres psql -d telebot -a -f "/telebot-server/230821-telethon-geolocate/sql/schema.sql"

apt install python3.11 python3-pip python3.11-venv


sudo -i -u telebot-user python3.11 -m venv venv
sudo -i -u telebot-user source ./venv/bin/activate
sudo -i -u telebot-user pip install -r ./requirements.txt


cp "./systemd/geospambot.service" "./systemd/lib/user/geospambot.service"
systemctl daemon-reload
systemctl enable geospambot
systemctl start geospambot
