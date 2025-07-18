import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar
import requests
import io
from openpyxl import load_workbook

st.set_page_config(page_title="Portail Extranet", layout="wide")

st.title("📆 Portail Extranet – Gestion des Réservations")

FILE_PATH = "reservations.xlsx"

# ---- SMS CONFIG ---- #
FREE_SMS_ENDPOINT = "https://smsapi.free-mobile.fr/sendmsg"
FREE_CONFIG = [
    {"user": "12026027", "key": "MF7Qjs3C8KxKHz"},
    {"user": "12026027", "key": "1Pat6vSRCLiSXl"},
]

# ---- Charger le fichier ---- #
@st.cache_data
def charger_donnees():
    df = pd.read_excel(FILE_PATH)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"])
    df["date_depart"] = pd.to_datetime(df["date_depart"])
    return df

# ---- Envoi SMS ---- #
def envoyer_sms(message):
    journal = []
    for config in FREE_CONFIG:
        payload = {"user": config["user"], "pass": config["key"], "msg": message}
        r = requests.get(FREE_SMS_ENDPOINT, params=payload)
        statut = "✅ Envoyé" if r.status_code == 200 else f"❌ Échec ({r.status_code})"
        journal.append(f"{config['user']}: {statut}")
    return journal

# ---- Sauvegarder ---- #
def sauvegarder_donnees(df):
    df.to_excel(FILE_PATH, index=False)

# ---- Onglets ---- #
onglet = st.tabs(["📋 Réservations", "📅 Calendrier", "➕ Ajouter une réservation"])

# === ONGLET 1 : RESERVATIONS === #
with onglet[0]:
    st.subheader("📋 Liste des réservations")
    df = charger_donnees()
    st.dataframe(df, use_container_width=True)

    st.download_button("📥 Télécharger Excel", data=df.to_csv(index=False), file_name="reservations.csv")

# === ONGLET 2 : CALENDRIER === #
with onglet[1]:
    st.subheader("📅 Calendrier mensuel des réservations")
    mois = st.selectbox("Mois", range(1, 13), index=datetime.datetime.now().month - 1)
    annee = st.selectbox("Année", range(2023, 2031), index=1)
    mois_nom = calendar.month_name[mois]

    cal = calendar.Calendar()
    df = charger_donnees()
    jours_mois = [day for day in cal.itermonthdates(annee, mois) if day.month == mois]

    planning = {jour: [] for jour in jours_mois}

    for _, row in df.iterrows():
        debut = row["date_arrivee"].date()
        fin = row["date_depart"].date()
        client = row["nom_client"]
        plateforme = row["plateforme"]
        couleur = "🔵" if plateforme == "Airbnb" else "🟢" if plateforme == "Booking" else "🔴"
        for jour in planning:
            if debut <= jour < fin:
                planning[jour].append(f"{couleur} {client}")

    # Affichage tableau calendrier
    cols = st.columns(7)
    jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    for i, jour_nom in enumerate(jours_semaine):
        cols[i].markdown(f"**{jour_nom}**")

    rows = [jours_mois[i:i+7] for i in range(0, len(jours_mois), 7)]
    for semaine in rows:
        row_cols = st.columns(7)
        for i, jour in enumerate(semaine):
            contenu = "\n".join(planning[jour])
            row_cols[i].markdown(f"**{jour.day}**\n{contenu}")

# === ONGLET 3 : AJOUTER === #
with onglet[2]:
    st.subheader("➕ Ajouter une réservation")

    with st.form("ajout_resa"):
        nom = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
        telephone = st.text_input("Téléphone du client")
        prix_brut = st.text_input("Prix brut (€)")
        prix_net = st.text_input("Prix net (€)")
        charges = st.text_input("Charges (€)")
        pourcentage = st.text_input("%")

        submit = st.form_submit_button("Enregistrer ✅")

        if submit:
            nouvelle = pd.DataFrame([{
                "nom_client": nom,
                "date_arrivee": pd.to_datetime(date_arrivee),
                "date_depart": pd.to_datetime(date_depart),
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcentage,
            }])
            df = charger_donnees()
            df = pd.concat([df, nouvelle], ignore_index=True)
            sauvegarder_donnees(df)
            st.success("✅ Réservation ajoutée et enregistrée")

# === SMS AUTOMATIQUE : ENVOI 24H AVANT === #
aujourd_hui = datetime.date.today()
demain = aujourd_hui + timedelta(days=1)
df = charger_donnees()
df_demain = df[df["date_arrivee"].dt.date == demain]

if not df_demain.empty:
    st.info("📩 SMS automatique aux clients arrivant demain")
    for _, row in df_demain.iterrows():
        message = (
            f"Bonjour {row['nom_client']},\n"
            f"Nous sommes heureux de vous accueillir demain à Nice.\n"
            f"Un emplacement de parking est à votre disposition sur place.\n"
            f"Merci de nous indiquer votre heure d’arrivée.\n"
            f"Bon voyage et à demain !\n"
            f"Annick & Charley"
        )
        journal = envoyer_sms(message)
        with st.expander(f"📨 Journal SMS – {row['nom_client']}"):
            for ligne in journal:
                st.write(ligne)

