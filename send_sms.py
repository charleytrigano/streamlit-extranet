import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# Configuration API Free Mobile
USER = "12026027"  # Numéro client Free
API_KEY = "MF7Qjs3C8KxKHz"

# Fichier des réservations
FICHIER_RESERVATIONS = "reservations.xlsx"
# Fichier pour stocker l'historique des SMS
FICHIER_HISTORIQUE = "historique_sms.csv"

def charger_reservations():
    df = pd.read_excel(FICHIER_RESERVATIONS)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date
    return df

def charger_historique():
    if os.path.exists(FICHIER_HISTORIQUE):
        return pd.read_csv(FICHIER_HISTORIQUE)
    else:
        return pd.DataFrame(columns=["date_envoi", "nom_client", "telephone", "message"])

def enregistrer_sms(nom, telephone, message):
    historique = charger_historique()
    nouvelle_entree = {
        "date_envoi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nom_client": nom,
        "telephone": telephone,
        "message": message
    }
    historique = pd.concat([historique, pd.DataFrame([nouvelle_entree])], ignore_index=True)
    historique.to_csv(FICHIER_HISTORIQUE, index=False)

def envoyer_sms(numero, message):
    try:
        url = f"https://smsapi.free-mobile.fr/sendmsg"
        params = {
            "user": USER,
            "pass": API_KEY,
            "msg": message
        }
        response = requests.get(url, params=params, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Erreur d'envoi : {e}")
        return False

def notifier_clients():
    df = charger_reservations()
    demain = (datetime.today() + timedelta(days=1)).date()

    df_notif = df[df["date_arrivee"] == demain]
    if df_notif.empty:
        print("Aucun client à notifier pour demain.")
        return

    for _, row in df_notif.iterrows():
        nom = row.get("nom_client", "")
        tel = str(row.get("telephone", "")).replace(" ", "").replace(".", "").strip()
        plateforme = row.get("plateforme", "")
        arrivee = row.get("date_arrivee")
        depart = row.get("date_depart")

        if not tel.startswith("+33") and tel.startswith("0"):
            tel = "+33" + tel[1:]  # Conversion format international

        message = (
            f"VILLA TOBIAS - {plateforme}\n"
            f"Bonjour {nom}. Votre séjour est prévu du {arrivee} au {depart}. "
            "Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. "
            "Nous vous rappelons qu'un parking est à votre disposition sur place. A demain"
        )

        print(f"Envoi à {nom} ({tel})...")
        succes = envoyer_sms(tel, message)
        if succes:
            enregistrer_sms(nom, tel, message)
            print("✅ SMS envoyé")
        else:
            print("❌ Échec d'envoi")

if __name__ == "__main__":
    notifier_clients()