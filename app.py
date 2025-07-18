import streamlit as st
import pandas as pd
import calendar
import datetime
import requests
from io import BytesIO
from datetime import timedelta

st.set_page_config(page_title="Portail Extranet", layout="wide")

st.title("🏨 Portail Extranet Streamlit")
st.markdown("---")

# Fonction pour charger les données
@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier. Détails :\n\n{e}")
        return None

# Fonction d'envoi SMS Free
def envoyer_sms(message):
    utilisateurs = [
        {"user": "12026027", "api_key": "MF7Qjs3C8KxKHz"},
        {"user": "12026027", "api_key": "1Pat6vSRCLiSXl"}  # second numéro
    ]
    for u in utilisateurs:
        try:
            url = f"https://smsapi.free-mobile.fr/sendmsg?user={u['user']}&pass={u['api_key']}&msg={message}"
            requests.get(url)
        except Exception as e:
            st.warning(f"Erreur envoi SMS à {u['user']} : {e}")

# Onglets
tab1, tab2, tab3 = st.tabs(["📋 Réservations", "📅 Calendrier", "➕ Nouvelle réservation"])

# 📋 Onglet 1 — Réservations
with tab1:
    st.subheader("📋 Réservations à venir")
    uploaded_file = st.file_uploader("Importer un fichier .xlsx", type="xlsx")

    if uploaded_file:
        df = load_data(uploaded_file)

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(sorted(required_cols))}")
        else:
            st.success("✅ Données chargées")
            st.dataframe(df, use_container_width=True)

            # Envoi SMS aux clients arrivant demain
            demain = pd.Timestamp.today().normalize() + timedelta(days=1)
            df_demain = df[df["date_arrivee"] == demain]

            if not df_demain.empty:
                for _, row in df_demain.iterrows():
                    msg = (
                        f"Bonjour {row['nom_client']},\n"
                        f"Nous sommes heureux de vous accueillir demain à Nice.\n"
                        f"Un emplacement de parking est à votre disposition sur place.\n"
                        f"Merci de nous indiquer votre heure approximative d'arrivée.\n"
                        f"Bon voyage et à demain !\n"
                        f"Annick & Charley"
                    )
                    envoyer_sms(msg)

            # Export Excel
            def convert_to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Réservations")
                return output.getvalue()

            st.download_button(
                "📥 Télécharger les données",
                data=convert_to_excel(df),
                file_name="reservations_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# 📅 Onglet 2 — Calendrier
with tab2:
    st.subheader("📅 Calendrier mensuel")

    if uploaded_file:
        df = load_data(uploaded_file)
        mois_actuel = st.selectbox("Choisir un mois", range(1, 13), index=datetime.datetime.now().month - 1)
        annee_actuelle = datetime.datetime.now().year

        if df is not None:
            try:
                df_filtered = df[(df["date_arrivee"].dt.month == mois_actuel) & (df["date_arrivee"].dt.year == annee_actuelle)]
                cal = calendar.Calendar()
                mois_cal = cal.monthdatescalendar(annee_actuelle, mois_actuel)

                plateforme_couleurs = {
                    "Airbnb": "#FFB6C1",
                    "Booking": "#87CEFA",
                    "Autre": "#90EE90"
                }

                st.markdown(f"### 📆 {calendar.month_name[mois_actuel]} {annee_actuelle}")
                for semaine in mois_cal:
                    cols = st.columns(7)
                    for i, jour in enumerate(semaine):
                        contenu = f"**{jour.day}**"
                        for _, row in df_filtered.iterrows():
                            if row["date_arrivee"].date() <= jour <= row["date_depart"].date():
                                couleur = plateforme_couleurs.get(row["plateforme"], "#D3D3D3")
                                contenu += f"<div style='background-color:{couleur};padding:3px;margin:1px;border-radius:4px'>{row['nom_client']}</div>"
                        cols[i].markdown(contenu, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erreur lors de la génération du calendrier : {e}")

# ➕ Onglet 3 — Ajout
with tab3:
    st.subheader("➕ Ajouter une nouvelle réservation")

    with st.form("ajout_reservation"):
        nom_client = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.text_input("Prix brut")
        prix_net = st.text_input("Prix net")
        charges = st.text_input("Charges")
        pourcentage = st.text_input("%")
        submitted = st.form_submit_button("Valider")

    if submitted and uploaded_file:
        new_row = {
            "nom_client": nom_client,
            "date_arrivee": pd.to_datetime(date_arrivee),
            "date_depart": pd.to_datetime(date_depart),
            "plateforme": plateforme,
            "telephone": telephone,
            "prix_brut": prix_brut,
            "prix_net": prix_net,
            "charges": charges,
            "%": pourcentage
        }

        try:
            df = load_data(uploaded_file)
            if df is not None:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("✅ Réservation ajoutée (temporairement)")
            else:
                st.error("Erreur lors du chargement.")
        except Exception as e:
            st.error(f"Erreur lors de l'ajout : {e}")

