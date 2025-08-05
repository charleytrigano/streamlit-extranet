import pandas as pd
import requests
from datetime import date, timedelta

# 📄 Fichier de données
FICHIER = "reservations.xlsx"

# 🔐 Identifiants API Free Mobile
API_USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUM_ADMIN = "+33617722379"  # Ton numéro

def envoyer_sms_clients():
    try:
        # 📥 Lecture du fichier Excel
        df = pd.read_excel(FICHIER)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date

        # 📅 Sélection des clients arrivant demain
        demain = date.today() + timedelta(days=1)
        df_notif = df[df["date_arrivee"] == demain]

        # ✉️ Envoi des SMS
        for _, row in df_notif.iterrows():
            tel_client = str(row["telephone"]).strip()
            if not tel_client.startswith("+"):
                tel_client = "+33" + tel_client[-9:]  # Format international

            message = (
                f"{row['plateforme']} - {row['nom_client']} - "
                f"{row['date_arrivee']} - {row['date_depart']}"
            )

            for numero in [tel_client, NUM_ADMIN]:
                try:
                    r = requests.get(
                        f"https://smsapi.free-mobile.fr/sendmsg",
                        params={"user": API_USER, "pass": API_KEY, "msg": message}
                    )
                    print(f"✅ SMS envoyé à {numero} : statut {r.status_code}")
                except Exception as e:
                    print(f"❌ Erreur envoi SMS à {numero} : {e}")

        if df_notif.empty:
            print("Aucun client avec arrivée demain.")
    except Exception as e:
        print(f"❌ Erreur générale : {e}")

if __name__ == "__main__":
    envoyer_sms_clients()