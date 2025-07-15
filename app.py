import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Portail Extranet Streamlit", page_icon="📅", layout="centered")

st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier `.csv` contenant les réservations à venir.")

# 📌 Configuration des identifiants Free Mobile
FREE_USER_1 = "12026027"
FREE_API_1 = "MF7Qjs3C8KxKHz"

FREE_USER_2 = "12026027"
FREE_API_2 = "1Pat6vSRCLiSXl"

# 📁 Importation du CSV
csv_file = st.file_uploader("Importer un fichier CSV", type="csv")

if csv_file is not None:
    try:
        df = pd.read_csv(csv_file, sep=";")

        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        if not required_cols.issubset(df.columns):
            st.error("❌ Le fichier doit contenir les colonnes : nom_client, date_arrivee, date_depart, plateforme, telephone")
        else:
            st.success("📋 Données chargées avec succès !")
            st.dataframe(df)

            # 📅 Visualisation du calendrier
            st.subheader("📆 Calendrier des réservations")
            df["nom_complet"] = df["nom_client"] + " (" + df["plateforme"] + ")"
            fig = px.timeline(
                df,
                x_start="date_arrivee",
                x_end="date_depart",
                y="nom_complet",
                color="plateforme"
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Client",
                title="Planning des séjours",
                height=600
            )
            st.plotly_chart(fig)

            # 📲 Envoi de SMS pour les arrivées de demain
            st.subheader("📲 SMS à envoyer (pour les arrivées de demain)")
            demain = datetime.now() + timedelta(days=1)
            demain_str = demain.strftime("%Y-%m-%d")
            df_demain = df[df["date_arrivee"].dt.strftime("%Y-%m-%d") == demain_str]

            if df_demain.empty:
                st.info("Aucune arrivée prévue demain.")
            else:
                log_sms = []
                for _, row in df_demain.iterrows():
                    message_client = (
                        f"Bonjour {row['nom_client']}, Nous sommes heureux de vous accueillir demain à Nice. "
                        f"Un emplacement de parking est à votre disposition sur place. "
                        f"Merci de nous indiquer votre heure approximative d'arrivée afin que nous puissions nous rendre disponible. "
                        f"Bon voyage et à demain ! - Annick et Charley"
                    )

                    message_info = (
                        f"Reservation : {row['plateforme']}\n"
                        f"Client      : {row['nom_client']}\n"
                        f"Arrivée le  : {row['date_arrivee'].strftime('%Y-%m-%d')}\n"
                        f"Départ le   : {row['date_depart'].strftime('%Y-%m-%d')}"
                    )

                    # Envoi au client (Free API n’envoie qu’à un numéro Free configuré)
                    r_client = requests.get("https://smsapi.free-mobile.fr/sendmsg", params={
                        "user": FREE_USER_1,
                        "pass": FREE_API_1,
                        "msg": message_client
                    })

                    # Envoi à toi (résumé)
                    r_owner = requests.get("https://smsapi.free-mobile.fr/sendmsg", params={
                        "user": FREE_USER_2,
                        "pass": FREE_API_2,
                        "msg": message_info
                    })

                    statut_client = "✅ Envoyé au client" if r_client.status_code == 200 else f"❌ Erreur client ({r_client.status_code})"
                    statut_owner = "✅ Résumé envoyé" if r_owner.status_code == 200 else f"❌ Erreur résumé ({r_owner.status_code})"

                    log_sms.append({
                        "nom_client": row["nom_client"],
                        "telephone": row["telephone"],
                        "plateforme": row["plateforme"],
                        "date_arrivee": row["date_arrivee"].strftime("%Y-%m-%d"),
                        "date_depart": row["date_depart"].strftime("%Y-%m-%d"),
                        "statut_client": statut_client,
                        "statut_proprio": statut_owner,
                        "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                # 📄 Affichage du journal
                st.subheader("📜 Journal des envois de SMS")
                df_log = pd.DataFrame(log_sms)
                st.dataframe(df_log)

                # ⬇️ Téléchargement du journal
                st.download_button(
                    label="📥 Télécharger le journal (CSV)",
                    data=df_log.to_csv(index=False).encode("utf-8"),
                    file_name="journal_sms.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")



