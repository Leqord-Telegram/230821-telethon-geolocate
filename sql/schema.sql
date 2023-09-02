DROP TABLE IF EXISTS "sessions" CASCADE;
DROP TABLE IF EXISTS "spammed_users" CASCADE;

CREATE TABLE "public"."sessions" (
  "session_name" varchar(255) NOT NULL,
  "phone_number" varchar(255) NOT NULL,
  "latitude" float8 NOT NULL,
  "longitude" float8 NOT NULL,
  "delta_latitude" float8 NOT NULL DEFAULT 0,
  "delta_longitude" float8 NOT NULL DEFAULT 0,
  PRIMARY KEY ("session_name"),
  CONSTRAINT "phone_number_unique" UNIQUE ("phone_number")
);

CREATE TABLE "public"."spammed_users" (
  "id" int8 NOT NULL,
  "timestamp" timestamp,
  "bot_session" varchar(255),
  PRIMARY KEY ("id")
);

GRANT Delete, Insert, References, Select, Trigger, Truncate, Update ON TABLE "public"."sessions" TO "telebot_user";
GRANT Delete, Insert, References, Select, Trigger, Truncate, Update ON TABLE "public"."spammed_users" TO "telebot_user";