import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="📅 Extranet Réservations", layout="centered")
st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier .csv contenant les réservations à venir.")

# --- Upload CSV ---
csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        # Lecture avec séparateur point-virgule
        df = pd.read_csv(csv_file, sep=";")
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        required_cols = {
            "nom_client",
            "date_arrivee",
            "date_depart",
            "plateforme",
            "telephone",
            "prix_brut",
            "prix_net",
            "charges",
            "%"
        }

        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            st.success("📋 Données chargées :")
            st.dataframe(df)

            # Filtrer les arrivées de demain
            demain = datetime.today() + timedelta(days=1)
            df_demain = df[df["date_arrivee"].dt.date == demain.date()]

            if not df_demain.empty:
                st.subheader("📨 Envoyer un SMS de rappel")
                if st.button("Envoyer les SMS de rappel"):

                    messages_envoyes = []
                    erreurs = []

                    # Liste des administrateurs à prévenir (Free Mobile)
                    FREE_RECIPIENTS = [
                        {"user": "12026027", "key": "1Pat6vSRCLiSXl"},
                        {"user": "12026027", "key": "MF7Qjs3C8KxKHz"}
                    ]

                    for _, row in df_demain.iterrows():
                        nom = row["nom_client"]
                        arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
                        depart = row["date_depart"].strftime("%d/%m/%Y")
                        plateforme = row["plateforme"]

                        message = (
                            f"Bonjour {nom},\n"
                            "Nous sommes heureux de vous accueillir demain à Nice.\n"
                            "Un emplacement de parking est à votre disposition sur place.\n"
                            "Merci de nous indiquer votre heure approximative d’arrivée "
                            "afin que nous puissions nous rendre disponibles.\n"
                            "Bon voyage et à demain !\n\n"
                            "Annick et Charley"
                        )

                        # Envoi à chaque numéro admin
                        for recipient in FREE_RECIPIENTS:
                            params = {
                                "user": recipient["user"],
                                "pass": recipient["key"],
                                "msg": f"Réservation {plateforme} - {nom}\nArrivée : {arrivee} | Départ : {depart}"
                            }
                            try:
                                r = requests.get("https://smsapi.free-mobile.fr/sendmsg", params=params)
                                if r.status_code == 200:
                                    messages_envoyes.append(f"✅ SMS Free envoyé à {recipient['user']} pour {nom}")
                                else:
                                    erreurs.append(f"❌ Erreur Free ({recipient['user']}) : {r.text}")
                            except Exception as e:
                                erreurs.append(f"❌ Exception Free ({recipient['user']}) : {e}")

                    for m in messages_envoyes:
                        st.success(m)
                    for e in erreurs:
                        st.error(e)
            else:
                st.info("Aucune arrivée prévue demain.")

            # 🎨 Calendrier visuel
            st.subheader("🗓️ Calendrier des réservations")
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

            df["Séjour"] = df["nom_client"] + " (" + df["plateforme"] + ")"
            fig = px.timeline(
                df,
                x_start="date_arrivee",
                x_end="date_depart",
                y="Séjour",
                color="plateforme",
                title="Calendrier des séjours",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="Client", height=600)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier : {e}")

st.caption("Développé avec ❤️ par Charley Trigano")




