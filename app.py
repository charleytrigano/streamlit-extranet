import streamlit as st
import pandas as pd
import requests
import plotly.figure_factory as ff
from datetime import datetime, timedelta

st.set_page_config(page_title="Extranet Réservations", layout="wide")
st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier **.xlsx** contenant les réservations à venir.")

# --------------------------
# Paramètres pour Free Mobile
# --------------------------
FREE_API_1 = {
    "user": "12026027",
    "key": "1Pat6vSRCLiSXl",
    "telephone": "+33617722379"
}
FREE_API_2 = {
    "user": "12026027",
    "key": "MF7Qjs3C8KxKHz",
    "telephone": "+33611772793"
}

# --------------------------
# Import du fichier .xlsx
# --------------------------
csv_file = st.file_uploader("📁 Importer un fichier XLSX", type=["xlsx"])

if csv_file is not None:
    try:
        df = pd.read_excel(csv_file)

        # Nettoyage des dates
        df["date_arrivee"] = pd.to_date(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_date(df["date_depart"], errors="coerce")

        # Colonnes requises
        required_cols = {
            "nom_client", "date_arrivee", "date_depart",
            "plateforme", "telephone",
            "prix_brut", "prix_net", "charges", "%"
        }

        if not required_cols.issubset(df.columns):
            st.error("❌ Le fichier doit contenir les colonnes : " + ", ".join(required_cols))
        else:
            st.success("✅ Fichier chargé avec succès.")
            st.dataframe(df)

            # --------------------------
            # ENVOI DE SMS 24h avant
            # --------------------------
            demain = datetime.now().date() + timedelta(days=1)
            df_demain = df[df["date_arrivee"].dt.date == demain]

            if not df_demain.empty:
                st.subheader("📤 Envoi des SMS prévus pour demain")

                for _, row in df_demain.iterrows():
                    message = f"""Bonjour {row['nom_client']} 👋

Nous sommes heureux de vous accueillir demain à Nice.
🅿️ Un emplacement de parking est à votre disposition sur place.

Merci de nous indiquer votre heure approximative d’arrivée
afin que nous puissions nous rendre disponible.

📅 Réservation via {row['plateforme']}
⏱️ Arrivée : {row['date_arrivee'].date()} 
🏁 Départ : {row['date_depart'].date()}

Bon voyage et à demain !
— Annick & Charley"""

                    for free_api in [FREE_API_1, FREE_API_2]:
                        try:
                            r = requests.get(
                                f"https://smsapi.free-mobile.fr/sendmsg",
                                params={
                                    "user": free_api["user"],
                                    "pass": free_api["key"],
                                    "msg": message
                                }
                            )
                            if r.status_code == 200:
                                st.success(f"📨 SMS envoyé à {free_api['telephone']}")
                            else:
                                st.error(f"❌ Erreur envoi vers {free_api['telephone']} — Code : {r.status_code}")
                        except Exception as e:
                            st.error(f"❌ Exception : {e}")
            else:
                st.info("Aucun client prévu pour demain.")

            # --------------------------
            # CALENDRIER VISUEL
            # --------------------------
            st.subheader("🗓️ Calendrier des réservations")

            calendrier_data = []
            color_map = {
                "Airbnb": "rgb(255, 127, 80)",
                "Booking": "rgb(100, 149, 237)",
                "Autre": "rgb(144, 238, 144)"
            }

            for _, row in df.iterrows():
                plateforme = row["plateforme"]
                couleur = color_map.get(plateforme, "gray")

                calendrier_data.append(dict(
                    Task=f"{row['nom_client']} ({plateforme})",
                    Start=str(row["date_arrivee"].date()),
                    Finish=str(row["date_depart"].date()),
                    Resource=plateforme
                ))

            fig = ff.create_gantt(
                calendrier_data,
                index_col='Resource',
                colors=color_map,
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                title="📅 Réservations du mois",
                bar_width=0.3
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur : {e}")



