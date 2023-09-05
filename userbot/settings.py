import tomllib
import os


class BotGlobalSettings:
    def __init__(self, settings_file_path: str):
        f = open(settings_file_path, "rb")
        data = tomllib.load(f)

        self.settings_file_path = settings_file_path
        
        self.period_messages_max = None
        if "period_messages_max" in data["limits"]:
            self.period_messages_max = data["limits"]["period_messages_max"]

        self.system_version = "4.16.30-vxTTSGA"
        if "system_version" in data["limits"]:
            self.system_version = data["limits"]["system_version"]

        self.period_messages_max = None
        if "period_messages_max" in data["limits"]:
            self.period_messages_max = data["limits"]["period_messages_max"]
        
        self.period_time_s = 24*60*60
        if "period_time_s" in data["limits"]:
            self.period_time_s = data["limits"]["period_time_s"]
        
        self.flood_error_delay_s = 4*60*60
        if "flood_error_delay_s" in data["limits"]:
            self.flood_error_delay_s = data["limits"]["flood_error_delay_s"]
        
        self.message_typing_start_delay_min_s = 1
        if "message_typing_start_delay_min_s" in data["limits"]:
            self.message_typing_start_delay_min_s = data["limits"]["message_typing_start_delay_min_s"]

        self.message_typing_start_delay_max_s = 4
        if "message_typing_start_delay_max_s" in data["limits"]:
            self.message_typing_start_delay_max_s = data["limits"]["message_typing_start_delay_max_s"]

        self.message_send_delay_min_s = 3
        if "message_send_delay_min_s" in data["limits"]:
            self.message_send_delay_min_s = data["limits"]["message_send_delay_min_s"]

        self.message_send_delay_max_s = 8
        if "message_send_delay_max_s" in data["limits"]:
            self.message_send_delay_max_s = data["limits"]["message_send_delay_max_s"]

        self.user_spam_delay_min_s = 16
        if "user_spam_delay_min_s" in data["limits"]:
            self.user_spam_delay_min_s = data["limits"]["user_spam_delay_min_s"]

        self.user_spam_delay_max_s = 32
        if "user_spam_delay_max_s" in data["limits"]:
            self.user_spam_delay_max_s = data["limits"]["user_spam_delay_max_s"]

        self.geoscan_delay_min_s = 30
        if "geoscan_delay_min_s" in data["limits"]:
            self.geoscan_delay_min_s = data["limits"]["geoscan_delay_min_s"]

        self.geoscan_delay_max_s = 80
        if "geoscan_delay_max_s" in data["limits"]:
            self.geoscan_delay_max_s = data["limits"]["geoscan_delay_max_s"]

        self.skipped_user_spam_delay_min_s = 80
        if "skipped_user_spam_delay_min_s" in data["limits"]:
            self.skipped_user_spam_delay_min_s = data["limits"]["skipped_user_spam_delay_min_s"]

        self.skipped_user_spam_delay_max_s = 80
        if "skipped_user_spam_delay_max_s" in data["limits"]:
            self.skipped_user_spam_delay_max_s = data["limits"]["skipped_user_spam_delay_max_s"]

        self.location_expiration = None
        if "location_expiration" in data["limits"]:
            self.location_expiration = data["limits"]["location_expiration"]

        self.accuracy_radius = 500
        if "lcoation" in data:
            if "accuracy_radius" in data["location"]:
                self.accuracy_radius = data["location"]["accuracy_radius"]

        

        self.api_id = data["auth"]["api_id"]
        self.api_hash = data["auth"]["api_hash"]
        self.group_hash = data["auth"]["group_hash"]
        self.db_user = data["auth"]["db_user"]
        self.db_password = data["auth"]["db_password"]
        
        self.db_name = data["database"]["db_name"]
        self.db_host = data["database"]["db_host"]
        self.db_port = data["database"]["db_port"]
