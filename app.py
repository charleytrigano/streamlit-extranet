import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import requests
import calendar
import io

# ------------------- PARAMÈTRES SMS FREE ------------------- #
FREE_USER_1 = "12026027"
FREE_API_KEY_1 = "1Pat6vSRCLiSXl"
FREE_USER_2 = "12026027"  # Deuxième ligne pour future compatibilité
FREE_API_KEY_2 = "1Pat6vSRCLiSXl"
NUM_SMS_DESTINATAIRE_1 = "+33617722379"
NUM_SMS_DESTINATAIRE_2 = "+33611772793"

# ------------------- FONCTION ENVOI SMS ------------------- #
def envoyer_sms_free(user, api_key, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={api_key}&msg={requests.utils.quote(message)}"
    response = requests.get(url)
    return response.status_code == 200

# ------------------- INTERFACE PRINCIPALE ------------------- #
st.set_page_config(page_title="Portail Extranet", layout="wide")
st.title("🏨 Portail Extranet - Annick & Charley")

# ------------------- ONGLET NAVIGATION ------------------- #
onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "➕ Nouvelle réservation", "📅 Calendrier"])

# ------------------- CHARGEMENT DES DONNÉES ------------------- #
@st.cache_data
def load_data(fichier):
    try:
        df = pd.read_excel(fichier)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return None

fichier_xlsx = st.file_uploader("📤 Importer le fichier .xlsx", type=["xlsx"], key="upload")
df = load_data(fichier_xlsx) if fichier_xlsx else None

# ------------------- ONGLET : RÉSERVATIONS ------------------- #
if onglet == "📋 Réservations":
    st.subheader("📋 Tableau des réservations")
    if df is not None:
        st.dataframe(df)

        # SMS 24h avant
        aujourd_hui = pd.Timestamp(datetime.date.today())
        demain = aujourd_hui + timedelta(days=1)
        df_demain = df[df["date_arrivee"] == demain]

        for _, row in df_demain.iterrows():
            message = (
                f"Bonjour {row['nom_client']},\n"
                "Nous sommes heureux de vous accueillir demain à Nice.\n"
                "Un emplacement de parking est à votre disposition sur place.\n"
                "Merci de nous indiquer votre heure approximative d'arrivée.\n"
                "Bon voyage et à demain !\nAnnick & Charley"
            )
            envoyer_sms_free(FREE_USER_1, FREE_API_KEY_1, message)
            envoyer_sms_free(FREE_USER_2, FREE_API_KEY_2, message)

        # Bouton de téléchargement
        def convert_to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Réservations")
            return output.getvalue()

        st.download_button(
            label="📥 Télécharger les réservations",
            data=convert_to_excel(df),
            file_name="reservations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("📂 Veuillez importer un fichier Excel valide.")

# ------------------- ONGLET : NOUVELLE RÉSERVATION ------------------- #
elif onglet == "➕ Nouvelle réservation":
    st.subheader("➕ Ajouter une nouvelle réservation")

    with st.form("ajout_reservation"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom du client")
            plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
            telephone = st.text_input("Téléphone")
        with col2:
            date_arrivee = st.date_input("Date d'arrivée")
            date_depart = st.date_input("Date de départ")

        prix_brut = st.text_input("Prix brut")
        prix_net = st.text_input("Prix net")
        charges = st.text_input("Charges")
        pourcentage = st.text_input("%")

        submit = st.form_submit_button("💾 Enregistrer la réservation")

        if submit and fichier_xlsx is not None and df is not None:
            nouvelle = pd.DataFrame([{
                "nom_client": nom,
                "date_arrivee": pd.to_datetime(date_arrivee),
                "date_depart": pd.to_datetime(date_depart),
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcentage
            }])
            df = pd.concat([df, nouvelle], ignore_index=True)
            st.success("✅ Réservation ajoutée. Pour enregistrer, téléchargez le fichier.")
            st.dataframe(df)

            st.download_button(
                label="📥 Télécharger les réservations mises à jour",
                data=convert_to_excel(df),
                file_name="reservations_mises_a_jour.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ------------------- ONGLET : CALENDRIER ------------------- #
elif onglet == "📅 Calendrier":
    st.subheader("📅 Calendrier des réservations")
    if df is not None:
        try:
            import plotly.figure_factory as ff

            # Couleur par plateforme
            couleurs = {
                "Booking": "rgb(0, 102, 204)",
                "Airbnb": "rgb(255, 51, 102)",
                "Autre": "rgb(0, 204, 102)"
            }

            tasks = []
            for _, row in df.iterrows():
                if pd.notna(row["date_arrivee"]) and pd.notna(row["date_depart"]):
                    tasks.append(dict(
                        Task=row["nom_client"],
                        Start=row["date_arrivee"],
                        Finish=row["date_depart"],
                        Resource=row["plateforme"]
                    ))

            fig = ff.create_gantt(tasks, index_col="Resource", show_colorbar=True, group_tasks=True, colors=couleurs, title="Gantt des séjours")
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur lors de la génération du calendrier : {e}")
    else:
        st.warning("📂 Veuillez importer un fichier Excel pour afficher le calendrier.")
