import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="📆 Extranet Calendrier + SMS", layout="centered")

st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier `.csv` contenant les réservations à venir.")

# Upload du fichier CSV
csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        # Lire avec séparateur ";"
        df = pd.read_csv(csv_file, sep=";")

        # Convertir les dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        # Colonnes attendues
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        optional_cols = {"prix_brut", "prix_net", "charges", "%"}

        if not required_cols.issubset(df.columns):
            st.error("❌ Le fichier doit contenir les colonnes : nom_client, date_arrivee, date_depart, plateforme, telephone")
            st.stop()

        st.success("✅ Données chargées avec succès !")
        st.dataframe(df)

        # Filtrer les réservations de demain
        demain = datetime.now() + timedelta(days=1)
        demain_str = demain.strftime("%Y-%m-%d")
        df_demain = df[df["date_arrivee"].dt.strftime("%Y-%m-%d") == demain_str]

        if not df_demain.empty:
            st.subheader("📨 Envoi des SMS pour les arrivées de demain")

            # Message personnalisé
            for index, row in df_demain.iterrows():
                message = (
                    f"Bonjour {row['nom_client']} 👋\n"
                    f"Nous sommes heureux de vous accueillir demain à Nice.\n"
                    f"Un emplacement de parking est à votre disposition sur place.\n"
                    f"Merci de nous indiquer votre heure approximative d'arrivée.\n"
                    f"Arrivée : {row['date_arrivee'].date()} / Départ : {row['date_depart'].date()}\n"
                    f"Plateforme : {row['plateforme']}\n\n"
                    f"Bon voyage et à demain !\nAnnick & Charley"
                )

                # Liste des destinataires Free Mobile
                destinataires = [
                    {"user": "12026027", "key": "MF7Qjs3C8KxKHz"},
                    {"user": "12026027", "key": "1Pat6vSRCLiSXl"}  # second destinataire
                ]

                for dest in destinataires:
                    url = f"https://smsapi.free-mobile.fr/sendmsg?user={dest['user']}&pass={dest['key']}&msg={requests.utils.quote(message)}"
                    response = requests.get(url)
                    if response.status_code == 200:
                        st.success(f"✅ SMS envoyé à {row['nom_client']}")
                    else:
                        st.error(f"❌ Erreur d'envoi SMS pour {row['nom_client']}")

        else:
            st.info("📭 Aucun client prévu demain.")

        # --------- CALENDRIER ---------
        st.subheader("📅 Visualisation des réservations")

        df["nom_affichage"] = df["nom_client"] + " (" + df["plateforme"] + ")"
        fig = px.timeline(
            df,
            x_start="date_arrivee",
            x_end="date_depart",
            y="nom_affichage",
            color="plateforme",
            title="Planning des réservations"
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Une erreur est survenue : {e}")

    st.write("🧪 Colonnes détectées :", df.columns.tolist())
    df = pd.read_csv(csv_file, sep=";")







