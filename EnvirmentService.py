import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import json


class EnvirmentService:
    def __init__(self):
        load_dotenv()
        self.consumer_key = os.getenv("CONSUMER_KEY")
        self.consumer_secret = os.getenv("CONSUMER_SECRET")

        self.auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)

        with open('./urls.json', 'r') as file:
            self.urls = json.load(file)