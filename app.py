import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import os

st.set_page_config(page_title="Portail Extranet", layout="wide")
st.title("📆 Portail Extranet - Calendrier & SMS")

# Charger le fichier existant
EXCEL_FILE = "reservations.xlsx"

def load_data():
    try:
        df = pd.read_excel(EXCEL_FILE)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return pd.DataFrame()

def save_data(df):
    try:
        df.to_excel(EXCEL_FILE, index=False)
        st.success("✅ Réservation ajoutée et sauvegardée.")
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")

df = load_data()

# ⏱️ AJOUT D’UNE RÉSERVATION
st.sidebar.header("➕ Ajouter une réservation")
with st.sidebar.form("add_form"):
    nom_client = st.text_input("Nom du client")
    date_arrivee = st.date_input("Date d'arrivée")
    date_depart = st.date_input("Date de départ")
    plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
    telephone = st.text_input("Téléphone (format : +336...)", max_chars=20)
    prix_brut = st.text_input("Prix brut (€)")
    prix_net = st.text_input("Prix net (€)")
    charges = st.text_input("Charges (€)")
    pourcentage = st.text_input("Commission (%)")
    submitted = st.form_submit_button("📥 Enregistrer")

    if submitted:
        new_row = pd.DataFrame([{
            "nom_client": nom_client,
            "date_arrivee": pd.to_datetime(date_arrivee),
            "date_depart": pd.to_datetime(date_depart),
            "plateforme": plateforme,
            "telephone": telephone,
            "prix_brut": prix_brut,
            "prix_net": prix_net,
            "charges": charges,
            "%": pourcentage
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)

# 📊 AFFICHAGE CALENDRIER TYPE GANTT
st.subheader("📅 Calendrier des réservations (vue Gantt)")
try:
    df_cal = df.dropna(subset=["date_arrivee", "date_depart", "nom_client"])
    df_cal["Durée"] = (df_cal["date_depart"] - df_cal["date_arrivee"]).dt.days
    fig = px.timeline(
        df_cal,
        x_start="date_arrivee",
        x_end="date_depart",
        y="nom_client",
        color="plateforme",
        title="Planning des séjours",
        hover_data=["plateforme", "prix_net"]
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Erreur lors de l'affichage du calendrier : {e}")

# 📤 ENVOI DE SMS (FREE MOBILE)
st.subheader("📩 Journal d’envoi de SMS - clients arrivant demain")
if "sms_log" not in st.session_state:
    st.session_state.sms_log = []

demain = datetime.now().date() + timedelta(days=1)
df_sms = df[df["date_arrivee"].dt.date == demain]

FREE_NUMEROS = [
    {"user": "12026027", "key": "1Pat6vSRCLiSXl"},
    {"user": "12026027", "key": "MF7Qjs3C8KxKHz"},
]

for _, row in df_sms.iterrows():
    nom = row["nom_client"]
    date_arr = row["date_arrivee"].strftime("%d/%m/%Y")
    date_dep = row["date_depart"].strftime("%d/%m/%Y")
    message = (
        f"Bonjour {nom},\n"
        "Nous sommes heureux de vous accueillir demain à Nice.\n"
        "Un emplacement de parking est à votre disposition sur place.\n"
        "Merci de nous indiquer votre heure d'arrivée approximative.\n"
        "Bon voyage et à demain !\nAnnick & Charley"
    )

    for dest in FREE_NUMEROS:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={dest['user']}&pass={dest['key']}&msg={requests.utils.quote(message)}"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                st.session_state.sms_log.append(f"✅ SMS envoyé à {nom}")
            else:
                st.session_state.sms_log.append(f"❌ Échec SMS à {nom} - Code {r.status_code}")
        except Exception as e:
            st.session_state.sms_log.append(f"❌ Erreur pour {nom} : {e}")

st.write("📋 Journal d’envoi de SMS :")
for line in st.session_state.sms_log:
    st.write(line)

# 📌 AFFICHAGE DU TABLEAU DES RÉSERVATIONS
st.subheader("📄 Tableau des réservations actuelles")
st.dataframe(df, use_container_width=True)
