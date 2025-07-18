import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import datetime, timedelta
import requests
import os

st.set_page_config(page_title="Extranet Réservations", layout="wide")

# ------------------------- CONFIGURATION SMS -------------------------
FREE_API_KEYS = {
    "+33617722379": "MF7Qjs3C8KxKHz",      # Numéro 1
    "+33611772793": "1Pat6vSRCLiSXl",      # Numéro 2
}
FREE_USER = "12026027"

# ------------------------- CHARGEMENT DU FICHIER -------------------------
st.sidebar.title("📁 Import des données")
fichier_excel = st.sidebar.file_uploader("Importer le fichier .xlsx", type=["xlsx"])

if fichier_excel:
    df = pd.read_excel(fichier_excel)

    # Vérification des colonnes attendues
    colonnes_attendues = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
                          "prix_brut", "prix_net", "charges", "%"}
    if not colonnes_attendues.issubset(set(df.columns)):
        st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(colonnes_attendues)}")
        st.stop()

    # Nettoyage dates
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

    st.success("✅ Données chargées avec succès")

    onglet = st.selectbox("🧭 Choisir une vue :", ["📋 Tableau", "🗓️ Calendrier", "➕ Nouvelle Réservation"])

    # ------------------------- ONGLET TABLEAU -------------------------
    if onglet == "📋 Tableau":
        st.subheader("📋 Réservations")
        st.dataframe(df)

        # 📩 SMS automatique
        demain = (datetime.today() + timedelta(days=1)).date()
        df_demain = df[df["date_arrivee"].dt.date == demain]

        if not df_demain.empty:
            st.subheader("📩 Envoi des SMS clients pour demain")

            for _, row in df_demain.iterrows():
                msg = (
                    f"Bonjour {row['nom_client']},\n\n"
                    "Nous sommes heureux de vous accueillir demain à Nice.\n"
                    "Un emplacement de parking est à votre disposition sur place.\n"
                    "Merci de nous indiquer votre heure approximative d'arrivée.\n"
                    "Bon voyage et à demain !\n"
                    "Annick & Charley"
                )

                for numero, key in FREE_API_KEYS.items():
                    payload = {
                        "user": FREE_USER,
                        "pass": key,
                        "msg": msg
                    }
                    try:
                        r = requests.get("https://smsapi.free-mobile.fr/sendmsg", params=payload)
                        if r.status_code == 200:
                            st.success(f"✅ SMS envoyé à {numero}")
                        else:
                            st.error(f"❌ Erreur pour {numero} : {r.text}")
                    except Exception as e:
                        st.error(f"❌ Exception pour {numero} : {e}")

    # ------------------------- ONGLET CALENDRIER -------------------------
    elif onglet == "🗓️ Calendrier":
        st.subheader("🗓️ Calendrier des réservations (mensuel)")

        df_cal = []
        for _, row in df.iterrows():
            arrivee = row["date_arrivee"]
            depart = row["date_depart"]
            if pd.notnull(arrivee) and pd.notnull(depart):
                jours = pd.date_range(arrivee, depart - timedelta(days=0)).date
                for jour in jours:
                    df_cal.append({
                        "date": jour,
                        "client": row["nom_client"],
                        "plateforme": row["plateforme"]
                    })

        if df_cal:
            df_visu = pd.DataFrame(df_cal)
            color_map = {
                "Airbnb": "#FF5A5F",
                "Booking": "#003580",
                "Autre": "#00A699"
            }

            fig = px.timeline(
                df_visu,
                x_start="date",
                x_end="date",
                y="client",
                color="plateforme",
                color_discrete_map=color_map,
                title="Planning des réservations",
                labels={"client": "Nom du client"}
            )
            fig.update_layout(
                xaxis=dict(title="Date", tickformat="%d %b"),
                yaxis=dict(autorange="reversed"),
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune réservation à afficher dans le calendrier.")

    # ------------------------- ONGLET AJOUT -------------------------
    elif onglet == "➕ Nouvelle Réservation":
        st.subheader("➕ Ajouter une réservation")

        with st.form("ajout_resa"):
            nom = st.text_input("Nom du client")
            arrivee = st.date_input("Date d’arrivée")
            depart = st.date_input("Date de départ", min_value=arrivee + timedelta(days=1))
            plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
            tel = st.text_input("Téléphone", placeholder="+336...")
            brut = st.text_input("Prix brut (€)")
            net = st.text_input("Prix net (€)")
            charges = st.text_input("Charges (€)")
            pourcent = st.text_input("%")

            submitted = st.form_submit_button("💾 Enregistrer")

            if submitted:
                nouvelle_resa = {
                    "nom_client": nom,
                    "date_arrivee": pd.to_datetime(arrivee),
                    "date_depart": pd.to_datetime(depart),
                    "plateforme": plateforme,
                    "telephone": tel,
                    "prix_brut": brut,
                    "prix_net": net,
                    "charges": charges,
                    "%": pourcent
                }
                df = pd.concat([df, pd.DataFrame([nouvelle_resa])], ignore_index=True)
                st.success("✅ Réservation ajoutée (non sauvegardée).")

                # Export automatique (optionnel)
                df.to_excel("reservations_updated.xlsx", index=False)
                st.info("💾 Nouvelle version enregistrée dans `reservations_updated.xlsx`")

else:
    st.warning("📂 Veuillez importer un fichier Excel (.xlsx) pour démarrer.")





