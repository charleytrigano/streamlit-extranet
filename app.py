import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="📆 Extranet - Calendrier & SMS", layout="wide")

st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier `.csv` contenant les réservations à venir.")

# Upload du fichier CSV
csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        # Lire le fichier CSV avec le bon séparateur
        df = pd.read_csv(csv_file, sep=";")

        # Nettoyage des dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        # Colonnes attendues
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        optional_cols = {"prix_brut", "prix_net", "charges", "%"}

        if not required_cols.issubset(df.columns):
            st.error("❌ Le fichier doit contenir les colonnes : nom_client, date_arrivee, date_depart, plateforme, telephone")
        else:
            # Alerte si des colonnes optionnelles manquent
            missing_optional = optional_cols - set(df.columns)
            if missing_optional:
                st.warning(f"⚠️ Colonnes optionnelles absentes : {', '.join(missing_optional)}")

            st.success("📋 Données chargées avec succès !")

            # Affichage des données
            st.dataframe(df)

            # ---------------------------
            # PARTIE : ENVOI DE SMS FREE
            # ---------------------------

            st.markdown("---")
            st.subheader("📱 Envoi de SMS pour les arrivées de demain")

            # Calcul date de demain
            demain = datetime.date.today() + datetime.timedelta(days=1)
            demain_str = pd.to_datetime(demain).normalize()

            df_demain = df[df["date_arrivee"].dt.normalize() == demain_str]

            if df_demain.empty:
                st.info("Aucun client prévu pour demain.")
            else:
                st.write(f"{len(df_demain)} client(s) prévu(s) pour le {demain.strftime('%d/%m/%Y')}")

                if st.button("📨 Envoyer les SMS"):
                    sms_logs = []

                    for _, row in df_demain.iterrows():
                        nom = row["nom_client"]
                        date_arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
                        date_depart = row["date_depart"].strftime("%d/%m/%Y")
                        plateforme = row["plateforme"]
                        numero_client = str(row["telephone"])

                        # Message à envoyer
                        message = (
                            f"Bonjour {nom},\n"
                            f"Nous sommes heureux de vous accueillir demain à Nice.\n"
                            f"Un emplacement de parking est à votre disposition sur place.\n"
                            f"Merci de nous indiquer votre heure approximative d'arrivée.\n"
                            f"Bon voyage et à demain !\n"
                            f"Annick & Charley"
                        )

                        # Paramètres Free SMS
                        free_users = [
                            {
                                "user": "12026027",
                                "key": "MF7Qjs3C8KxKHz"
                            },
                            {
                                "user": "12026027",
                                "key": "1Pat6vSRCLiSXl"
                            }
                        ]

                        for user_data in free_users:
                            url = (
                                f"https://smsapi.free-mobile.fr/sendmsg?user={user_data['user']}"
                                f"&pass={user_data['key']}&msg={requests.utils.quote(message)}"
                            )
                            response = requests.get(url)
                            if response.status_code == 200:
                                sms_logs.append(f"✅ SMS envoyé à {user_data['user']}")
                            else:
                                sms_logs.append(f"❌ Erreur pour {user_data['user']} : {response.status_code}")

                    st.text_area("📤 Résultat de l'envoi SMS", "\n".join(sms_logs), height=150)

            # ---------------------------
            # PARTIE : CALENDRIER PLOTLY
            # ---------------------------

            st.markdown("---")
            st.subheader("📅 Calendrier des réservations")

            if not df.empty:
                df["nom_affichage"] = df["nom_client"] + " (" + df["plateforme"] + ")"
                fig = px.timeline(
                    df,
                    x_start="date_arrivee",
                    x_end="date_depart",
                    y="nom_affichage",
                    color="plateforme",
                    title="Vue chronologique des réservations"
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(height=600, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de la lecture du fichier : {str(e)}")





