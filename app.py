import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# ---------------------------
# PARAMÈTRES API Free Mobile
# ---------------------------
FREE_USER = "12026027"
FREE_API_KEY = "MF7Qjs3C8KxKHz"

st.set_page_config(page_title="Portail Extranet Streamlit", layout="centered")
st.title("📆 Calendrier des Réservations + SMS Rappel")

st.markdown("Importez un fichier `.csv` contenant les réservations.")
csv_file = st.file_uploader("📎 Importer un fichier CSV", type="csv")

if csv_file is not None:
    try:
        # Lire le fichier CSV avec le bon séparateur
        df = pd.read_csv(csv_file, sep=";")
        
        # Nettoyage des dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            st.success("✅ Données chargées avec succès.")
            st.dataframe(df)

            # 🗓️ Affichage calendrier
            st.subheader("📅 Visualisation des réservations")
            df_gantt = df.rename(columns={
                "nom_client": "Task",
                "date_arrivee": "Start",
                "date_depart": "Finish",
                "plateforme": "Resource"
            })

            fig = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Resource")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

            # 🔔 SMS automatiques
            st.subheader("📩 Envoi automatique de SMS aux clients arrivant demain")

            demain = datetime.today() + timedelta(days=1)
            demain_str = demain.strftime("%Y-%m-%d")
            df_demain = df[df["date_arrivee"] == demain_str]

            if not df_demain.empty:
                for _, row in df_demain.iterrows():
                    message = f"Bonjour {row['nom_client']}, nous vous attendons demain dans votre logement réservé sur {row['plateforme']}."
                    numero = str(row['telephone'])

                    url = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER}&pass={FREE_API_KEY}&msg={message}"

                    try:
                        response = requests.get(url)
                        if response.status_code == 200:
                            st.success(f"✅ SMS envoyé à {numero}")
                        else:
                            st.error(f"❌ Échec pour {numero} (code {response.status_code})")
                    except Exception as e:
                        st.error(f"❌ Erreur pour {numero} : {str(e)}")
            else:
                st.info("Aucune arrivée prévue demain. Aucun SMS envoyé.")

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier : {e}")

