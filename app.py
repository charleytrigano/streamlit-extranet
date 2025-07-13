import streamlit as st
import pandas as pd
import datetime
import os
from twilio.rest import Client

st.set_page_config(page_title="Extranet · Rappels SMS", layout="centered")

st.title("📩 Envoi automatique de SMS aux clients")
st.markdown("Importez un fichier `.csv` contenant les réservations à venir.")

uploaded_file = st.file_uploader("Importer un fichier CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("📋 Données chargées :")
    st.dataframe(df)

    required_columns = {"nom_client", "date_arrivee", "telephone"}

    if not required_columns.issubset(df.columns):
        st.error("Le fichier doit contenir les colonnes : nom_client, date_arrivee, telephone")
    else:
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        df_tomorrow = df[df["date_arrivee"].dt.date == tomorrow]

        st.write(df_tomorrow)

        if df_tomorrow.empty:
            st.warning(f"Aucun client avec une arrivée prévue le {tomorrow}.")
        else:
            st.success(f"{len(df_tomorrow)} client(s) arrivent demain ({tomorrow}).")

            if st.button("📤 Envoyer les SMS de rappel"):
                sid = os.environ.get("TWILIO_SID")
                token = os.environ.get("TWILIO_TOKEN")
                sender = os.environ.get("TWILIO_NUMBER")

                if not all([sid, token, sender]):
                    st.error("Clés Twilio manquantes. Vérifiez vos secrets dans Streamlit Cloud.")
                else:
                    client = Client(sid, token)
                    for _, row in df_tomorrow.iterrows():
                        try:
                            msg = f"Bonjour {row['nom_client']}, votre arrivée est prévue demain. À bientôt !"
                            message = client.messages.create(
                                body=msg,
                                from_=sender,
                                to=row["telephone"]
                            )
                            st.success(f"✅ SMS envoyé à {row['nom_client']} ({row['telephone']})")
                        except Exception as e:
                            st.error(f"❌ Erreur pour {row['telephone']} : {e}")

