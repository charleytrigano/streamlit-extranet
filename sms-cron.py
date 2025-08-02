import pandas as pd
import requests
from datetime import date, datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

FICHIER = "reservations.xlsx"
JOURNAL = "journal_sms.log"

# 📒 Charger les données de réservation
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df = df[df["date_arrivee"].notna()]
    df["nom_client"] = df["nom_client"].fillna("Client")
    df["plateforme"] = df["plateforme"].fillna("Autre")
    return df

# 📨 Envoi du SMS via l'API Free
def envoyer_sms(user, key, message, identifiant):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={message}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            log(f"✅ SMS envoyé à {identifiant}")
        else:
            log(f"⚠️ Erreur lors de l'envoi du SMS à {identifiant} (code {response.status_code})")
    except Exception as e:
        log(f"❌ Exception pour {identifiant} : {e}")

# ✅ Journalisation
def log(message, destinataire=None, type_sms=None, date_obj=None):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(JOURNAL, "a") as f:
        f.write(f"{timestamp} {message}\n")
        if destinataire and type_sms and date_obj:
            tag = f"{destinataire}_{type_sms}_{date_obj.strftime('%Y-%m-%d')}"
            f.write(f"{tag}\n")
    print(f"{timestamp} {message}")

def deja_envoye(destinataire, type_sms, date_obj):
    tag = f"{destinataire}_{type_sms}_{date_obj.strftime('%Y-%m-%d')}"
    if os.path.exists(JOURNAL):
        with open(JOURNAL, "r") as f:
            return tag in f.read()
    return False

# 📤 Traitement principal
def envoyer_sms_jour():
    if not is_connected():
        print("⚠️ Pas de connexion internet.")
        return

    df = charger_donnees()
    demain = date.today() + timedelta(days=1)
    df_sms = df[df["date_arrivee"].dt.date == demain]

    # 🧾 Message client
    for _, row in df_sms.iterrows():
        nom = row["nom_client"]
        numero = str(row["telephone"])
        if pd.notna(numero) and not deja_envoye(nom, "client", demain):
            message = (
                f"Bonjour {nom},\n"
                f"Nous sommes heureux de vous accueillir demain à Nice via {row['plateforme']}.\n"
                f"Un emplacement de parking est à votre disposition.\n"
                f"Merci de nous indiquer votre heure approximative d’arrivée.\n"
                f"Bon voyage et à demain !\n"
                f"Annick & Charley"
            )
            envoyer_sms(os.getenv("FREE_USER"), os.getenv("FREE_API_KEY"), message, nom)
            log(f"SMS envoyé à {nom}", destinataire=nom, type_sms="client", date_obj=demain)

    # 📩 Message administrateurs
    admin_list = [
        {
            "user": "12026027",
            "key": "MF7Qjs3C8KxKHz",
            "label": "Admin1"
        },
        {
            "user": "12026027",
            "key": "1Pat6vSRCLiSXl",
            "label": "Admin2"
        }
    ]

    if not df_sms.empty:
        admin_message = "🛎️ Arrivées prévues demain :\n"
        for _, row in df_sms.iterrows():
            admin_message += f"- {row['nom_client']} via {row['plateforme']}\n"

        for admin in admin_list:
            if not deja_envoye(admin["label"], "admin", demain):
                envoyer_sms(admin["user"], admin["key"], admin_message.strip(), admin["label"])
                log(f"Résumé envoyé à {admin['label']}", destinataire=admin["label"], type_sms="admin", date_obj=demain)

# 🌍 Vérifie la connexion internet
def is_connected():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except:
        return False

# ▶️ Exécution
if __name__ == "__main__":
    envoyer_sms_jour()
