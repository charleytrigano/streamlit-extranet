import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly.express as px
import os

# ------------------ CONFIGURATION ------------------
st.set_page_config(page_title="Extranet - Réservations", layout="wide")
st.title("📅 Portail Extranet - Gestion des réservations")

# Fichier Excel
FICHIER_XLSX = "reservations.xlsx"

# Configuration SMS Free Mobile
FREE_USER_1 = "12026027"
FREE_KEY_1 = "1Pat6vSRCLiSXl"
FREE_USER_2 = "12026027"
FREE_KEY_2 = "1Pat6vSRCLiSXl"

def envoyer_sms(message):
    erreurs = []
    for user, key in [(FREE_USER_1, FREE_KEY_1), (FREE_USER_2, FREE_KEY_2)]:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={message}"
        try:
            r = requests.get(url)
            if r.status_code != 200:
                erreurs.append(f"❌ Erreur pour {user} : {r.status_code}")
        except Exception as e:
            erreurs.append(f"❌ Exception pour {user} : {e}")
    return erreurs

# ------------------ CHARGEMENT ------------------

@st.cache_data
def charger_donnees(path):
    df = pd.read_excel(path)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    return df

# ------------------ AFFICHAGE DU TABLEAU ------------------

def afficher_tableau(df):
    st.subheader("📋 Tableau des réservations")
    st.dataframe(df)

# ------------------ CALENDRIER ------------------

def afficher_calendrier(df):
    st.subheader("📆 Calendrier mensuel")

    try:
        fig = px.timeline(
            df,
            x_start="date_arrivee",
            x_end="date_depart",
            y="nom_client",
            color="plateforme",
            title="Planning des séjours",
            labels={"nom_client": "Client"},
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de la génération du calendrier : {e}")

# ------------------ SMS AUTOMATIQUE ------------------

def sms_pour_demain(df):
    demain = datetime.now().date() + timedelta(days=1)
    df_demain = df[df["date_arrivee"].dt.date == demain]

    if df_demain.empty:
        st.info("Aucun client n'arrive demain.")
        return

    st.subheader("📩 Envoi automatique de SMS")

    for _, row in df_demain.iterrows():
        msg = (
            f"Bonjour {row['nom_client']},\n"
            "Nous sommes heureux de vous accueillir demain à Nice.\n"
            "Un emplacement de parking est à votre disposition sur place.\n"
            "Merci de nous indiquer votre heure approximative d’arrivée.\n"
            "Bon voyage et à demain !\n"
            "Annick & Charley"
        )
        erreurs = envoyer_sms(msg)
        if erreurs:
            for e in erreurs:
                st.error(e)
        else:
            st.success(f"📤 SMS envoyé pour {row['nom_client']}")

# ------------------ FORMULAIRE AJOUT ------------------

def ajouter_reservation(df):
    st.subheader("➕ Ajouter une nouvelle réservation")

    with st.form("ajouter_resa"):
        nom = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.text_input("Prix brut (€)")
        prix_net = st.text_input("Prix net (€)")
        charges = st.text_input("Charges (€)")
        pourcentage = st.text_input("%")

        valider = st.form_submit_button("Valider")
        if valider:
            nouvelle_ligne = {
                "nom_client": nom,
                "date_arrivee": pd.to_datetime(date_arrivee),
                "date_depart": pd.to_datetime(date_depart),
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcentage,
            }
            df = df._append(nouvelle_ligne, ignore_index=True)
            df.to_excel(FICHIER_XLSX, index=False)
            st.success("✅ Réservation ajoutée avec succès.")
            st.rerun()

# ------------------ INTERFACE PRINCIPALE ------------------

if not os.path.exists(FICHIER_XLSX):
    st.warning("📂 Aucun fichier de réservation trouvé.")
    uploaded_file = st.file_uploader("Importez un fichier .xlsx", type="xlsx")
    if uploaded_file:
        with open(FICHIER_XLSX, "wb") as f:
            f.write(uploaded_file.read())
        st.success("Fichier importé. Rechargez la page.")
else:
    df = charger_donnees(FICHIER_XLSX)

    onglet = st.sidebar.radio("Navigation", ["Tableau", "Calendrier", "Ajouter", "SMS Demain"])

    if onglet == "Tableau":
        afficher_tableau(df)
    elif onglet == "Calendrier":
        afficher_calendrier(df)
    elif onglet == "Ajouter":
        ajouter_reservation(df)
    elif onglet == "SMS Demain":
        sms_pour_demain(df)
