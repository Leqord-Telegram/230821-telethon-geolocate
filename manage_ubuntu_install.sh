#!/bin/bash

echo "User telebot-user should have been created! useradd -m -U telebot-user"

apt install postgresql postgresql-contrib
systemctl enable postgresql
systemctl start postgresql

sleep 15

sudo -i -u postgres psql -U postgres -a -f "./sql/init.sql"
sudo -i -u postgres psql -U postgres -d telebot -a -f "./sql/schema.sql"

apt install python3 python3-pip python3-venv


sudo -i -u telebot-user python -m venv venv
sudo -i -u telebot-user source venv/bin/activate
sudo -i -u telebot-user pip install -r ./requirements.txt


cp "./systemd/geospambot.service" "./systemd/lib/user/geospambot.service"
systemctl daemon-reload
systemctl enable geospambot
systemctl start geospambot

