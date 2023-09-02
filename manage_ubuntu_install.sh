echo "User telebot-user should have been created! useradd -m -U telebot-user"

apt install postgresql postgresql-contrib
systemctl enable postgresql
systemctl start postgresql

su postgres
psql -U postgres -a -f "./sql/init.sql"
psql -U postgres -d telebot -a -f "./sql/schema.sql"
exit

apt install python3 python3-pip python3-venv

su telebot-user
python -m venv venv
source venv/bin/activate
pip install -r ./requirements.txt


cp "./systemd/geospambot.service" "./systemd/lib/user/geospambot.service"
systemctl daemon-reload
systemctl enable geospambot
systemctl start geospambot

