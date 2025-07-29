import pandas as pd
from datetime import date, timedelta
import requests
import smtplib
import socket
from dotenv import load_dotenv
import os

load_dotenv()

FICHIER = "reservations.xlsx"

# 🔌 Vérifie si on a accès à Internet
def est_connecte():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# ✉️ Envoie un email de confirmation
def envoyer_email(sujet, message):
    try:
        import ssl
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = sujet
        msg["From"] = os.getenv("EMAIL_SENDER")
        msg["To"] = os.getenv("EMAIL_RECIPIENTS")
        msg.set_content(message)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)

        print("✅ Email envoyé")
    except Exception as e:
        print("❌ Erreur email :", e)

# 📲 Envoie un SMS via Free
def envoyer_sms(telephone, message, user, key):
    try:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={requests.utils.quote(message)}"
        r = requests.get(url)
        print(f"📤 SMS à {telephone} : {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print("❌ Erreur SMS :", e)
        return False

# 🚀 Script principal
def envoyer_sms_clients():
    if not est_connecte():
        print("⚠️ Pas de connexion internet.")
        return

    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")

    demain = date.today() + timedelta(days=1)
    df_sms = df[df["date_arrivee"].dt.date == demain]

    logs = []
    for _, row in df_sms.iterrows():
        nom = row["nom_client"]
        tel = row.get("telephone", "")
        plateforme = row.get("plateforme", "")
        if not tel:
            continue

        msg = (
            f"Bonjour {nom},\n"
            "Nous sommes heureux de vous accueillir demain à Nice.\n"
            "Un emplacement de parking est à votre disposition.\n"
            "Merci de nous indiquer votre heure approximative d’arrivée.\n"
            "Bon voyage et à demain !\n"
            "Annick & Charley"
        )

        success = envoyer_sms(tel, msg, os.getenv("FREE_USER"), os.getenv("FREE_API_KEY"))
        logs.append(f"{'✅' if success else '❌'} {nom} ({plateforme}) -> {tel}")

    # Envoi aux deux numéros administrateurs
    for admin, key in [
        ("+33617722371", "MF7Qjs3C8KxKHz"),
        ("+33611772793", "YA0TcGvUlYrHfa"),
    ]:
        log_admin = "\n".join(logs) or "Aucun client à notifier"
        envoyer_sms(admin, "📢 Journal des SMS envoyés :\n" + log_admin, admin, key)

    # Email récapitulatif
    envoyer_email(
        "Journal SMS Extranet",
        "\n".join(logs) or "Aucun SMS client à envoyer aujourd’hui."
    )

if __name__ == "__main__":
    envoyer_sms_clients()
