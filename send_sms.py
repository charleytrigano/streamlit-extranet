import sys
import requests

# Données API Free
API_KEY = "MF7Qjs3C8KxKHz"
USER_ID = "12026027"

numero = sys.argv[1]
message = sys.argv[2]

url = f"https://smsapi.free-mobile.fr/sendmsg?user={USER_ID}&pass={API_KEY}&msg={message}"

try:
    r = requests.get(url)
    r.raise_for_status()
except Exception as e:
    print("Erreur d'envoi :", e)