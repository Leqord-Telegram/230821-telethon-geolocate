CREATE ROLE "telebot_user" LOGIN ENCRYPTED PASSWORD 'password';

CREATE DATABASE "telebot" ENCODING = 'UTF8';

GRANT Connect ON DATABASE "telebot" TO "telebot_user";