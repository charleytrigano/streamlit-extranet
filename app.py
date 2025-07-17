import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import requests
from datetime import datetime, timedelta
import os

st.set_page_config(layout="wide")
st.title("📅 Portail Extranet avec Calendrier & SMS")

# --- Fonctions ---
def envoyer_sms_free(user, api_key, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={api_key}&msg={requests.utils.quote(message)}"
    try:
        r = requests.get(url)
        return r.status_code == 200
    except Exception as e:
        return False

def charger_donnees():
    try:
        df = pd.read_excel("reservations.xlsx")
        colonnes_requises = {'nom_client', 'date_arrivee', 'date_depart', 'plateforme', 'telephone',
                             'prix_brut', 'prix_net', 'charges', '%'}
        if not colonnes_requises.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(colonnes_requises)}")
            return pd.DataFrame()
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        return df.dropna(subset=["date_arrivee", "date_depart"])
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return pd.DataFrame()

def enregistrer_donnees(df):
    df.to_excel("reservations.xlsx", index=False)

# --- Charger données ---
st.subheader("📋 Données actuelles")
df = charger_donnees()

if not df.empty:
    st.dataframe(df)

# --- Ajouter une réservation ---
st.subheader("➕ Ajouter une réservation")
with st.form("ajouter"):
    nom_client = st.text_input("Nom du client")
    date_arrivee = st.date_input("Date d'arrivée")
    date_depart = st.date_input("Date de départ")
    plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
    telephone = st.text_input("Téléphone")
    prix_brut = st.text_input("Prix brut")
    prix_net = st.text_input("Prix net")
    charges = st.text



