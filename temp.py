import requests

name = "Anjali Kawatra"
response = requests.get(f"https://api.genderize.io?name={name}")
print(response.json())
