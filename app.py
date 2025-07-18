import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Extranet Streamlit", layout="wide")
st.title("🏨 Récapitulatif des Réservations + SMS Automatique")

# 🔁 Upload du fichier
st.subheader("📂 Importer le fichier .xlsx")
file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])

if file:
    try:
        df = pd.read_excel(file)
        required_cols = {
            "nom_client", "date_arrivee", "date_depart", "plateforme",
            "telephone", "prix_brut", "prix_net", "charges", "%"
        }
        if not required_cols.issubset(set(df.columns)):
            st.error("❌ Le fichier doit contenir les colonnes : " + ", ".join(required_cols))
        else:
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
            st.success("✅ Fichier chargé avec succès.")
            st.dataframe(df)

            # ✅ GANTT CALENDAR
            st.subheader("📅 Calendrier des Réservations (Gantt)")
            try:
                fig = px.timeline(
                    df,
                    x_start="date_arrivee",
                    x_end="date_depart",
                    y="nom_client",
                    color="plateforme",
                    hover_data=["plateforme", "prix_net"]
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur lors de la génération du calendrier : {e}")

            # ✅ ENVOI DE SMS FREE MOBILE
            st.subheader("📩 Envoi de SMS aux clients arrivant demain")

            demain = datetime.now().date() + timedelta(days=1)
            df_demain = df[df["date_arrivee"].dt.date == demain]

            if not df_demain.empty:
                for _, row in df_demain.iterrows():
                    nom = row["nom_client"]
                    date_arr = row["date_arrivee"].strftime("%d/%m/%Y")
                    date_dep = row["date_depart"].strftime("%d/%m/%Y")
                    telephone = row["telephone"]

                    message = (
                        f"Bonjour {nom},\n"
                        "Nous sommes heureux de vous accueillir demain à Nice.\n"
                        "Un emplacement de parking est à votre disposition sur place.\n"
                        "Merci de nous indiquer votre heure d'arrivée approximative.\n"
                        "Bon voyage et à demain !\nAnnick & Charley"
                    )

                    for api_key in ["MF7Qjs3C8KxKHz", "1Pat6vSRCLiSXl"]:
                        user = "12026027"
                        url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={api_key}&msg={requests.utils.quote(message)}"
                        try:
                            r = requests.get(url)
                            if r.status_code == 200:
                                st.success(f"✅ SMS envoyé à {nom}")
                            else:
                                st.warning(f"⚠️ Échec SMS pour {nom} (code {r.status_code})")
                        except Exception as e:
                            st.error(f"❌ Erreur d'envoi SMS pour {nom} : {e}")
            else:
                st.info("📆 Aucun client n'arrive demain.")

    except Exception as e:
        st.error(f"❌ Erreur de traitement du fichier : {e}")
else:
    st.info("📁 Veuillez importer un fichier Excel au format attendu.")

