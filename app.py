import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# ---------------------------
# PARAMÈTRES API Free Mobile
# ---------------------------
FREE_USER = "12026027"  # Ton identifiant Free
FREE_API_KEY = "MF7Qjs3C8KxKHz"  # Ta clé API

# ---------------------------
# Configuration de la page
# ---------------------------
st.set_page_config(page_title="Portail Extranet Streamlit", page_icon="📆", layout="wide")

st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier `.csv` contenant les réservations à venir.")

# ---------------------------
# Import du fichier CSV
# ---------------------------
csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file:
    try:
        df = pd.read_csv(csv_file, sep=";")  # séparateur CSV FR
        st.success("✅ Fichier chargé avec succès !")
        st.write("📋 Données chargées :")
        st.dataframe(df)

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme"}
        if not required_cols.issubset(df.columns):
            st.error("❌ Le fichier doit contenir les colonnes : nom_client, date_arrivee, date_depart, plateforme")
        else:
            # Conversion des dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

            # --------- 📅 Affichage Calendrier -----------
            st.subheader("📆 Calendrier des réservations")
            df_cal = df.copy()
            df_cal["nom + plateforme"] = df["nom_client"] + " (" + df["plateforme"] + ")"

            fig = px.timeline(
                df_cal,
                x_start="date_arrivee",
                x_end="date_depart",
                y="nom + plateforme",
                color="plateforme",
                title="Réservations à venir",
            )
            fig.update_layout(xaxis_title="Dates", yaxis_title="Clients", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

            # --------- ✉️ ENVOI DES SMS -----------
            st.subheader("📲 Notification automatique des arrivées de demain")

            if st.button("📩 Envoyer les SMS clients arrivant demain"):
                demain = datetime.today().date() + timedelta(days=1)
                df_demain = df[df["date_arrivee"].dt.date == demain]

                if df_demain.empty:
                    st.info("Aucun client n’arrive demain.")
                else:
                    for _, row in df_demain.iterrows():
                        message = f"Bonjour {row['nom_client']}, nous vous attendons demain pour votre réservation via {row['plateforme']}."
                        url = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER}&pass={FREE_API_KEY}&msg={requests.utils.quote(message)}"
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                st.success(f"✅ SMS envoyé à {row['nom_client']}")
                            else:
                                st.error(f"❌ Échec SMS à {row['nom_client']} ({response.status_code})")
                        except Exception as e:
                            st.error(f"❌ Erreur pour {row['nom_client']} : {e}")
    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier : {e}")
