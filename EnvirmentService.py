import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import json
import mysql.connector
from datetime import datetime
import pytz
class EnvirmentService:
    def __init__(self):
        load_dotenv()
        self.consumer_key = os.getenv("CONSUMER_KEY")
        self.consumer_secret = os.getenv("CONSUMER_SECRET")
        self.application_password=os.getenv("APPLICATION_PASSWORD")
        self.application_username=os.getenv("APPLICATION_USERNAME")
        self.site_id=os.getenv("SITE_ID")
        self.db_host=os.getenv("DB_HOST") 
        self.db_username=os.getenv("DB_USERNAME")
        self.db_password=os.getenv("DB_PASSWORD")
        self.db_name=os.getenv("DATABASE")
        self.utc_timezone = pytz.UTC


        self.connection = mysql.connector.connect(
            host=self.db_host,
            user=self.db_username,
            password=self.db_password,
            database=self.db_name
        )
        if self.connection.is_connected():
            print("Connected to MySQL server")

        self.auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)

        with open('./urls.json', 'r') as file:
            self.urls = json.load(file)
    def get_corresponding_type(self, timestamp, interval_type="week", kind="%Y-%m-%dT%H:%M:%SZ"):
        dt_object = None

        # Convert timestamp to datetime object based on the requested type
        if interval_type == "week":
            dt_object = datetime.fromtimestamp(timestamp)
        
        elif interval_type == "date":
            dt_object = datetime.utcfromtimestamp(timestamp)
            # Assuming self.utc_timezone is defined for timezone conversion
            dt_object = self.utc_timezone.localize(dt_object)

        elif interval_type == "epoch":
            # If you want the timestamp in seconds (epoch)
            return timestamp

        elif interval_type == "custom":
            # If you want the timestamp in a custom format
            dt_object = datetime.fromtimestamp(timestamp)
        
        # If a custom kind is provided, apply it to format the date
        if interval_type in ["week", "date", "custom"]:
            normalized_value = dt_object.strftime(kind)
            return normalized_value

        return None