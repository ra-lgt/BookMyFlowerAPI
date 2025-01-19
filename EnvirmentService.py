import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import json
import mysql.connector

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