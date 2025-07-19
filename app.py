import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import calendar
import requests
import io
from pathlib import Path

# 📌 CONFIG
FICHIER_RESERVATIONS = "reservations.xlsx"
FREE_SMS_URL = "https://smsapi.free-mobile.fr/sendmsg"

# 📬 PARAMÈTRES SMS FREE
FREE_API_KEYS = {
    "+33617722379": "MF7Qjs3C8KxKHz",
    "+33611772793": "1Pat6vSRCLiSXl"
}
FREE_USER = "12026027"

# 📦 CHARGEMENT / SAUVEGARDE
def charger_reservations():
    if Path(FICHIER_RESERVATIONS).exists():
        df = pd.read_excel(FICHIER_RESERVATIONS)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"])
        df["date_depart"] = pd.to_datetime(df["date_depart"])
        return df
    else:
        return pd.DataFrame(columns=["nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
                                     "prix_brut", "prix_net", "charges", "%"])

def sauvegarder_reservations(df):
    df = df.sort_values("date_arrivee")
    df.to_excel(FICHIER_RESERVATIONS, index=False)

# ✉️ ENVOI DE SMS
def envoyer_sms(nom, date_arrivee, tel):
    message = f"Bonjour {nom}, nous sommes heureux de vous accueillir demain à Nice.\nUn emplacement de parking est à votre disposition.\nMerci de nous indiquer votre heure approximative d'arrivée.\nBon voyage et à demain !\nAnnick & Charley"
    for numero, cle in FREE_API_KEYS.items():
        payload = {"user": FREE_USER, "pass": cle, "msg": message}
        try:
            r = requests.get(FREE_SMS_URL, params=payload)
            if r.status_code == 200:
                st.success(f"✅ SMS envoyé à {numero}")
            else:
                st.error(f"❌ Échec SMS {numero} : Code {r.status_code}")
        except Exception as e:
            st.error(f"❌ Erreur envoi SMS à {numero} : {e}")

# 📆 AFFICHAGE CALENDRIER
def afficher_calendrier(df):
    st.subheader("📅 Calendrier mensuel")

    mois_nom = list(calendar.month_name)[1:]
    mois_index = mois_nom.index(st.selectbox("Mois", mois_nom)) + 1
    annee = st.selectbox("Année", list(range(2024, 2031)), index=1)

    plateforme_couleurs = {
        "Airbnb": "#FFB347",
        "Booking": "#87CEEB",
        "Abritel": "#90EE90",
        "Direct": "#FF69B4"
    }

    df_mois = df[
        (df["date_arrivee"].dt.month <= mois_index) &
        (df["date_depart"].dt.month >= mois_index) &
        (df["date_arrivee"].dt.year == annee)
    ]

    calendrier = {}
    for i in range(1, calendar.monthrange(annee, mois_index)[1] + 1):
        calendrier[date(annee, mois_index, i)] = []

    for _, row in df_mois.iterrows():
        debut = row["date_arrivee"].date()
        fin = row["date_depart"].date()
        for jour in calendrier:
            if debut <= jour < fin:
                plateforme = row["plateforme"]
                couleur = plateforme_couleurs.get(plateforme, "#D3D3D3")
                calendrier[jour].append((row["nom_client"], couleur))

    for semaine in calendar.Calendar().monthdatescalendar(annee, mois_index):
        cols = st.columns(7)
        for i, jour in enumerate(semaine):
            with cols[i]:
                if jour.month == mois_index:
                    st.markdown(f"**{jour.day}**")
                    for client, color in calendrier.get(jour, []):
                        st.markdown(f'<div style="background-color:{color};padding:2px;border-radius:3px;">{client}</div>', unsafe_allow_html=True)

# 📊 RAPPORT
def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    df["mois"] = df["date_arrivee"].dt.month
    df["année"] = df["date_arrivee"].dt.year
    regroupement = df.groupby(["année", "mois", "plateforme"]).agg({
        "prix_brut": "sum",
        "prix_net": "sum",
        "charges": "sum",
        "%": "mean"
    }).reset_index()

    regroupement["mois"] = regroupement["mois"].apply(lambda x: calendar.month_name[x])
    st.dataframe(regroupement)

# 🧾 GESTION RESERVATIONS
def afficher_tableau(df):
    st.subheader("📋 Réservations")
    st.dataframe(df)

    with st.form("formulaire_reservation", clear_on_submit=True):
        st.markdown("### ➕ Ajouter ou modifier une réservation")
        nom = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Abritel", "Direct"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.number_input("Prix brut", min_value=0.0)
        prix_net = st.number_input("Prix net", min_value=0.0)
        charges = st.number_input("Charges", min_value=0.0)
        pourcent = st.number_input("%", min_value=0.0, max_value=100.0)

        submit = st.form_submit_button("✅ Enregistrer la réservation")

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
                "%": pourcent
            }])
            df = pd.concat([df, nouvelle], ignore_index=True)
            sauvegarder_reservations(df)
            st.success("Réservation enregistrée avec succès ✅")

    st.markdown("---")
    st.markdown("### 🗑️ Supprimer une réservation")
    ligne = st.number_input("Numéro de ligne à supprimer", min_value=0, max_value=len(df)-1)
    if st.button("Supprimer"):
        df = df.drop(index=ligne).reset_index(drop=True)
        sauvegarder_reservations(df)
        st.success("Réservation supprimée ✅")

# 📩 ENVOI SMS AUTOMATIQUE
def envoyer_sms_arrivees_demain(df):
    st.subheader("📩 SMS pour les arrivées de demain")
    demain = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
    df_demain = df[df["date_arrivee"] == demain]

    if df_demain.empty:
        st.info("Aucun client n’arrive demain.")
    else:
        for _, row in df_demain.iterrows():
            envoyer_sms(row["nom_client"], row["date_arrivee"], row["telephone"])

# 🚀 APPLICATION PRINCIPALE
def main():
    st.set_page_config(page_title="Extranet Locations", layout="wide")
    st.title("🏨 Extranet Gestion Réservations")

    onglet = st.sidebar.radio("Navigation", ["Réservations", "Calendrier", "Rapport"])

    df = charger_reservations()

    if onglet == "Réservations":
        afficher_tableau(df)
        envoyer_sms_arrivees_demain(df)
    elif onglet == "Calendrier":
        afficher_calendrier(df)
    elif onglet == "Rapport":
        rapport_mensuel(df)

main()
