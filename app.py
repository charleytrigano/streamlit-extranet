import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from twilio.rest import Client
import os
from dotenv import load_dotenv

# 🔐 Chargement des identifiants Twilio depuis le fichier .env
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

client = Client(TWILIO_SID, TWILIO_TOKEN)

# ------------------------------
# Interface Streamlit
# ------------------------------
st.set_page_config(page_title="📅 Réservations Automatisées", layout="centered")
st.title("🏨 Récupération des données Airbnb & Booking")

st.markdown("Cette application vous permet d'importer vos réservations 📄 et de planifier un envoi de **SMS automatique** 📲.")

# ------------------------------
# Upload du fichier CSV
# ------------------------------
uploaded_file = st.file_uploader("📂 Importer vos réservations (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("📋 Réservations chargées :")
    st.dataframe(df)

    # ------------------------------
    # Filtrage : clients qui arrivent demain
    # ------------------------------
    demain = (datetime.now() + timedelta(days=1)).date()
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    arrivants = df[df["date_arrivee"] == demain]

    if not arrivants.empty:
        st.success(f"{len(arrivants)} client(s) prévu(s) pour demain ({demain})")
        st.dataframe(arrivants)

        # ------------------------------
        # Envoi de SMS
        # ------------------------------
        if st.button("📲 Envoyer tous les SMS maintenant"):
            for index, row in arrivants.iterrows():
                message = f"Bonjour {row['nom_client']} 👋, nous vous attendons demain pour votre séjour !"
                try:
                    sms = client.messages.create(
                        body=message,
                        from_=TWILIO_NUMBER,
                        to=row["telephone"]
                    )
                    st.success(f"✅ SMS envoyé à {row['nom_client']} ({row['telephone']})")
                except Exception as e:
                    st.error(f"❌ Erreur pour {row['nom_client']}: {e}")
    else:
        st.warning(f"Aucune réservation prévue pour demain ({demain})")

