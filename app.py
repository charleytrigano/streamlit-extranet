import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import requests
import os

FICHIER = "reservations.xlsx"
SMS_LOG = "sms_log.csv"

FREE_API_USER = "12026027"
FREE_API_KEY = "MF7Qjs3C8KxKHz"
NUM_ADMIN = "+33617722379"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        lignes = [texte[i:i+largeur_max] for i in range(0, len(texte), largeur_max)]
        for ligne in lignes:
            pdf.multi_cell(0, 8, ligne)
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

def envoyer_sms(numero, message):
    url = "https://smsapi.free-mobile.fr/sendmsg"
    params = {
        "user": FREE_API_USER,
        "pass": FREE_API_KEY,
        "msg": message
    }
    try:
        response = requests.get(url, params=params)
        return response.status_code == 200
    except:
        return False

def bouton_envoi_sms(df):
    st.subheader("📤 Envoi SMS")
    demain = (date.today() + timedelta(days=1))
    a_notifier = df[df["date_arrivee"] == demain]

    if a_notifier.empty:
        st.info("Aucun client n'arrive demain.")
        return

    for _, row in a_notifier.iterrows():
        nom = row["nom_client"]
        plateforme = row["plateforme"]
        arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
        depart = row["date_depart"].strftime("%d/%m/%Y")

        message = f"VILLA TOBIAS - {plateforme}\nBonjour {nom}. Votre séjour est prévu du {arrivee} au {depart}. Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. Nous vous rappelons qu’un parking est à votre disposition sur place. À demain"
        if st.button(f"📨 Envoyer à {nom}"):
            ok = envoyer_sms(NUM_ADMIN, message)
            if ok:
                log_sms(nom, plateforme, arrivee, depart, message)
                st.success(f"SMS envoyé à {nom}")
            else:
                st.error(f"Erreur lors de l’envoi du SMS à {nom}")

def log_sms(nom, plateforme, arrivee, depart, message):
    ligne = {
        "nom_client": nom,
        "plateforme": plateforme,
        "date_arrivee": arrivee,
        "date_depart": depart,
        "message": message,
        "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.DataFrame([ligne])
    if os.path.exists(SMS_LOG):
        ancien = pd.read_csv(SMS_LOG)
        df = pd.concat([ancien, df], ignore_index=True)
    df.to_csv(SMS_LOG, index=False)

def afficher_historique_sms():
    st.subheader("📨 Historique des SMS")
    if os.path.exists(SMS_LOG):
        df = pd.read_csv(SMS_LOG)
        st.dataframe(df)
    else:
        st.info("Aucun SMS encore envoyé.")

# Autres fonctions identiques aux versions précédentes
# ajouter_reservation, modifier_reservation, afficher_calendrier,
# rapport_mensuel, exporter_pdf, liste_clients

# ⬇️ Placez ici vos fonctions précédentes pour :
# - ajouter_reservation()
# - modifier_reservation()
# - afficher_calendrier()
# - rapport_mensuel()
# - liste_clients()

# ▶️ Application principale
def main():
    st.sidebar.title("📁 Menu")
    onglet = st.sidebar.radio("Navigation", [
        "📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer",
        "📅 Calendrier", "📊 Rapport", "👥 Liste Clients",
        "📤 SMS à envoyer", "📨 Historique SMS"
    ])

    df = charger_donnees()

    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df)
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)
    elif onglet == "👥 Liste Clients":
        liste_clients(df)
    elif onglet == "📤 SMS à envoyer":
        bouton_envoi_sms(df)
    elif onglet == "📨 Historique SMS":
        afficher_historique_sms()

if __name__ == "__main__":
    main()

import requests
from datetime import datetime

# 🔑 Identifiants API Free SMS
USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUMERO_PROPRIO = "+33617722379"
HISTORIQUE_SMS = "historique_sms.csv"

# ✉️ Envoi d’un SMS via l’API Free
def envoyer_sms(message, destinataire):
    url = "https://smsapi.free-mobile.fr/sendmsg"
    params = {
        "user": USER,
        "pass": API_KEY,
        "msg": message
    }
    if destinataire == NUMERO_PROPRIO:
        requests.get(url, params=params)

    # ⏺️ Sauvegarde de l’historique
    ligne = pd.DataFrame([{
        "date_envoi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "destinataire": destinataire,
        "message": message
    }])
    try:
        historique = pd.read_csv(HISTORIQUE_SMS)
        historique = pd.concat([historique, ligne], ignore_index=True)
    except FileNotFoundError:
        historique = ligne
    historique.to_csv(HISTORIQUE_SMS, index=False)