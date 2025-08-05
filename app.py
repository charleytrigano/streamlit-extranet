import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import os
import subprocess

FICHIER = "reservations.xlsx"
SMS_HISTORY_FILE = "sms_history.csv"

# 🔤 Nettoyage accents
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 🔁 Envoi SMS (via send_sms.py)
def envoyer_sms_via_script(numero, message):
    try:
        subprocess.run(["python", "send_sms.py", numero, message], check=True)
        enregistrer_sms_historique(numero, message)
        st.success(f"✅ SMS envoyé à {numero}")
    except subprocess.CalledProcessError:
        st.error("❌ Erreur lors de l'envoi du SMS")

# 📝 Historique SMS
def enregistrer_sms_historique(numero, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = pd.DataFrame([[now, numero, message]], columns=["Horodatage", "Numéro", "Message"])
    if os.path.exists(SMS_HISTORY_FILE):
        df = pd.read_csv(SMS_HISTORY_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
    else:
        df = new_entry
    df.to_csv(SMS_HISTORY_FILE, index=False)

# 📤 Génération du message personnalisé
def generer_message_sms(nom, plateforme, date_arrivee, date_depart):
    return (
        f"VILLA TOBIAS - {plateforme}\n"
        f"Bonjour {nom}. Votre séjour est prévu du {date_arrivee} au {date_depart}. "
        f"Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. "
        f"Nous vous rappelons qu'un parking est à votre disposition sur place. A demain"
    )

# 📋 Liste clients
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois = st.selectbox("Mois", sorted(df[df["annee"] == annee]["mois"].dropna().unique()))
    data = df[(df["annee"] == annee) & (df["mois"] == mois)]
    if not data.empty:
        data = data.copy()
        data["charges"] = (data["prix_brut"] - data["prix_net"]).round(2)
        data["%"] = (data["charges"] / data["prix_brut"] * 100).round(2).fillna(0)
        data["prix_brut_nuit"] = (data["prix_brut"] / data["nuitees"]).round(2).fillna(0)
        data["prix_net_nuit"] = (data["prix_net"] / data["nuitees"]).round(2).fillna(0)
        colonnes = [
            "nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees",
            "prix_brut", "prix_net", "charges", "%", "prix_brut_nuit", "prix_net_nuit"
        ]
        data = data[colonnes]
        st.dataframe(data)

        # Envoi SMS
        st.markdown("### 📨 Envoi d'un SMS")
        selected_client = st.selectbox("Choisissez un client", data["nom_client"])
        client = data[data["nom_client"] == selected_client].iloc[0]
        num = st.text_input("📱 Numéro du client (format international)", "+33")
        if st.button("📨 Envoyer SMS au client"):
            message = generer_message_sms(
                client["nom_client"],
                client["plateforme"],
                client["date_arrivee"].strftime("%d/%m/%Y"),
                client["date_depart"].strftime("%d/%m/%Y"),
            )
            envoyer_sms_via_script(num, message)
    else:
        st.info("Aucune donnée pour cette période.")

# 🕓 Onglet Historique SMS
def afficher_historique_sms():
    st.subheader("📜 Historique des SMS envoyés")
    if os.path.exists(SMS_HISTORY_FILE):
        df = pd.read_csv(SMS_HISTORY_FILE)
        st.dataframe(df)
    else:
        st.info("Aucun SMS envoyé pour le moment.")

# App
def main():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df["prix_brut"] = df["prix_brut"].round(2)
    df["prix_net"] = df["prix_net"].round(2)
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month

    onglet = st.sidebar.radio("📁 Menu", [
        "📋 Liste Clients",
        "📜 Historique SMS"
    ])

    if onglet == "📋 Liste Clients":
        liste_clients(df)
    elif onglet == "📜 Historique SMS":
        afficher_historique_sms()

if __name__ == "__main__":
    main()