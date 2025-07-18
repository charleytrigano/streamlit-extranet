import streamlit as st
import pandas as pd
import calendar
import datetime
import requests
from datetime import timedelta

st.set_page_config(page_title="Portail Extranet", layout="wide")

# ----------- Configuration SMS (Free Mobile) -----------
FREE_API_USER_1 = "12026027"
FREE_API_KEY_1 = "MF7Qjs3C8KxKHz"

FREE_API_USER_2 = "12026027"
FREE_API_KEY_2 = "1Pat6vSRCLiSXl"

NUMERO_FREE_1 = "+33617722379"
NUMERO_FREE_2 = "+33611772793"

# ----------- Fonctions Utilitaires -----------

def envoyer_sms_free(user, key, message):
    try:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={requests.utils.quote(message)}"
        r = requests.get(url)
        return r.status_code == 200
    except:
        return False

def convertir_dates(df):
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    return df

def afficher_tableau(df):
    st.dataframe(df)

def enregistrer_fichier(df, fichier_path="reservations.xlsx"):
    df.to_excel(fichier_path, index=False)

# ----------- Importation -----------
st.title("📅 Portail Extranet - Réservations")
fichier = st.file_uploader("Importer un fichier .xlsx", type=["xlsx"])

if fichier:
    try:
        df = pd.read_excel(fichier)
        required_columns = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not required_columns.issubset(set(df.columns)):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_columns)}")
            st.stop()

        df = convertir_dates(df)

        # ---------------- SMS ----------------
        aujourd_hui = pd.Timestamp.now().normalize()
        demain = aujourd_hui + timedelta(days=1)

        df_demain = df[df["date_arrivee"] == demain]
        for _, row in df_demain.iterrows():
            nom = row["nom_client"]
            date_arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
            message = (
                f"Bonjour {nom},\n\n"
                "Nous sommes heureux de vous accueillir demain à Nice.\n"
                "Un emplacement de parking est à votre disposition.\n"
                "Merci de nous indiquer votre heure approximative d’arrivée.\n"
                "Bon voyage et à demain !\nAnnick & Charley"
            )
            envoyer_sms_free(FREE_API_USER_1, FREE_API_KEY_1, message)
            envoyer_sms_free(FREE_API_USER_2, FREE_API_KEY_2, message)

        # ----------- Onglets Streamlit -----------
        onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "📆 Calendrier"])

        if onglet == "📋 Réservations":
            st.subheader("📋 Liste des réservations")
            afficher_tableau(df)

            st.markdown("### ➕ Ajouter une réservation")
            with st.form("ajouter_resa"):
                nom = st.text_input("Nom du client")
                date_a = st.date_input("Date d'arrivée")
                date_d = st.date_input("Date de départ", min_value=date_a + timedelta(days=1))
                plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
                tel = st.text_input("Téléphone")
                prix_brut = st.text_input("Prix brut")
                prix_net = st.text_input("Prix net")
                charges = st.text_input("Charges")
                pourcentage = st.text_input("%")
                submitted = st.form_submit_button("✅ Enregistrer")

                if submitted:
                    nouvelle = pd.DataFrame([{
                        "nom_client": nom,
                        "date_arrivee": pd.to_datetime(date_a),
                        "date_depart": pd.to_datetime(date_d),
                        "plateforme": plateforme,
                        "telephone": tel,
                        "prix_brut": prix_brut,
                        "prix_net": prix_net,
                        "charges": charges,
                        "%": pourcentage
                    }])
                    df = pd.concat([df, nouvelle], ignore_index=True)
                    enregistrer_fichier(df)
                    st.success("✅ Réservation ajoutée et enregistrée.")

            st.markdown("### 🛠️ Modifier ou Supprimer")
            noms = df["nom_client"].tolist()
            selected = st.selectbox("Sélectionner un client à modifier/supprimer", noms)
            row = df[df["nom_client"] == selected].iloc[0]

            with st.form("modifier_resa"):
                nom_m = st.text_input("Nom", row["nom_client"])
                date_a_m = st.date_input("Arrivée", row["date_arrivee"].date())
                date_d_m = st.date_input("Départ", row["date_depart"].date())
                plateforme_m = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(row["plateforme"]))
                tel_m = st.text_input("Téléphone", row["telephone"])
                brut_m = st.text_input("Prix brut", row["prix_brut"])
                net_m = st.text_input("Prix net", row["prix_net"])
                charges_m = st.text_input("Charges", row["charges"])
                pourcent_m = st.text_input("%", row["%"])
                modif = st.form_submit_button("✅ Modifier")
                suppr = st.form_submit_button("🗑️ Supprimer")

                if modif:
                    df.loc[df["nom_client"] == selected] = [
                        nom_m, date_a_m, date_d_m, plateforme_m, tel_m, brut_m, net_m, charges_m, pourcent_m
                    ]
                    enregistrer_fichier(df)
                    st.success("✏️ Réservation modifiée avec succès.")

                if suppr:
                    df = df[df["nom_client"] != selected]
                    enregistrer_fichier(df)
                    st.success("🗑️ Réservation supprimée.")

        elif onglet == "📆 Calendrier":
            st.subheader("📆 Calendrier des réservations (mensuel)")
            from calendar import monthrange

            mois = st.selectbox("Mois", list(calendar.month_name)[1:])
            annee = st.number_input("Année", min_value=2024, max_value=2030, value=datetime.datetime.now().year)

            try:
                mois_num = list(calendar.month_name).index(mois)
                nb_jours = monthrange(annee, mois_num)[1]
                calendrier = pd.DataFrame(columns=range(1, nb_jours + 1))

                plateformes_couleurs = {
                    "Airbnb": "lightblue",
                    "Booking": "lightgreen",
                    "Autre": "lightcoral"
                }

                for i, row in df.iterrows():
                    d1 = row["date_arrivee"].date()
                    d2 = row["date_depart"].date()
                    if d1.month == mois_num and d1.year == annee:
                        for jour in range(d1.day, d2.day):
                            calendrier.loc[row["nom_client"], jour] = row["plateforme"]

                def colorer(val):
                    if pd.isna(val): return ""
                    return f"background-color: {plateformes_couleurs.get(val, 'lightgray')}"

                st.dataframe(calendrier.style.applymap(colorer))
            except Exception as e:
                st.error(f"Erreur calendrier : {e}")
    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")
