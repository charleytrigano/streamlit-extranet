import streamlit as st
import pandas as pd
import datetime
import requests
from io import BytesIO
import calendar

# ----------------------------------------
# CONFIGURATION DES SMS (Free Mobile)
# ----------------------------------------

FREE_SMS_1 = {
    "user": "12026027",
    "api_key": "1Pat6vSRCLiSXl",
    "numero": "+33617722379"
}

FREE_SMS_2 = {
    "user": "12026027",
    "api_key": "1Pat6vSRCLiSXl",
    "numero": "+33611772793"
}

# Pour journaliser les SMS envoyés
sms_journal = []

# ----------------------------------------
# FONCTION : ENVOI DE SMS
# ----------------------------------------

def envoyer_sms_free(message):
    for destinataire in [FREE_SMS_1, FREE_SMS_2]:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={destinataire['user']}&pass={destinataire['api_key']}&msg={message}"
        try:
            r = requests.get(url)
            sms_journal.append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "to": destinataire["numero"],
                "status": "✅ Envoyé" if r.status_code == 200 else f"❌ Erreur {r.status_code}"
            })
        except Exception as e:
            sms_journal.append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "to": destinataire["numero"],
                "status": f"❌ Exception : {e}"
            })

# ----------------------------------------
# FONCTION : AFFICHAGE DU CALENDRIER
# ----------------------------------------

def generer_calendrier(df):
    st.subheader("📅 Calendrier des réservations")

    today = datetime.date.today()
    mois = st.selectbox("Choisir le mois", list(range(1, 13)), index=today.month - 1)
    annee = st.selectbox("Choisir l'année", list(range(today.year, today.year + 2)), index=0)

    mois_nom = calendar.month_name[mois]
    st.markdown(f"### {mois_nom} {annee}")

    cal = calendar.Calendar(firstweekday=0)
    jours_mois = cal.itermonthdates(annee, mois)

    couleurs = {
        "Booking": "#ffcccc",
        "Airbnb": "#ccffcc",
        "Autre": "#ccccff"
    }

    jours_html = ""

    for semaine in calendar.monthcalendar(annee, mois):
        jours_html += "<tr>"
        for jour in semaine:
            if jour == 0:
                jours_html += "<td></td>"
            else:
                date_jour = datetime.date(annee, mois, jour)
                contenu = ""
                for _, row in df.iterrows():
                    try:
                        if row['date_arrivee'].date() <= date_jour <= row['date_depart'].date():
                            couleur = couleurs.get(row['plateforme'], "#e0e0e0")
                            contenu += f"<div style='background-color:{couleur};padding:2px;margin:1px;font-size:12px;border-radius:4px;'>{row['nom_client']}</div>"
                    except:
                        continue
                jours_html += f"<td style='vertical-align: top; padding:4px; border: 1px solid #ccc; min-width: 100px; height: 80px;'><strong>{jour}</strong><br>{contenu}</td>"
        jours_html += "</tr>"

    st.markdown(
        f"""
        <table style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>Lun</th><th>Mar</th><th>Mer</th><th>Jeu</th><th>Ven</th><th>Sam</th><th>Dim</th>
            </tr>
            {jours_html}
        </table>
        """,
        unsafe_allow_html=True
    )

# ----------------------------------------
# INTERFACE STREAMLIT
# ----------------------------------------

st.set_page_config(page_title="Portail Extranet", layout="wide")
st.title("🏨 Portail Extranet Streamlit")

menu = st.sidebar.radio("📁 Navigation", ["📋 Réservations", "📅 Calendrier", "📤 Ajouter une réservation", "📨 Journal des SMS"])

if "df" not in st.session_state:
    st.session_state.df = None

if menu == "📋 Réservations":
    st.header("📋 Importer les réservations")
    fichier = st.file_uploader("Charger un fichier Excel (.xlsx)", type=["xlsx"])
    if fichier:
        try:
            df = pd.read_excel(fichier)
            required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
            if required_cols.issubset(df.columns):
                df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
                df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
                st.session_state.df = df
                st.success("✅ Fichier chargé avec succès")
                st.dataframe(df)
            else:
                st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(sorted(required_cols))}")
        except Exception as e:
            st.error(f"Erreur lors du traitement du fichier. Détails : {e}")

    # Envoi SMS pour arrivées le lendemain
    if st.session_state.df is not None:
        df = st.session_state.df
        demain = datetime.date.today() + datetime.timedelta(days=1)
        df_demain = df[df["date_arrivee"].dt.date == demain]
        if not df_demain.empty:
            for _, row in df_demain.iterrows():
                msg = f"Bonjour {row['nom_client']},\nNous sommes heureux de vous accueillir demain à Nice.\nUn emplacement de parking est à votre disposition.\nMerci de nous indiquer votre heure d'arrivée.\nBon voyage !\nAnnick & Charley"
                envoyer_sms_free(msg)
            st.success("✅ SMS envoyés pour les arrivées de demain.")

elif menu == "📅 Calendrier":
    if st.session_state.df is not None:
        try:
            generer_calendrier(st.session_state.df)
        except Exception as e:
            st.error(f"Erreur lors de la génération du calendrier : {e}")
    else:
        st.info("Veuillez importer un fichier Excel dans l'onglet Réservations.")

elif menu == "📤 Ajouter une réservation":
    st.header("📤 Ajouter une nouvelle réservation")
    with st.form("ajout_resa"):
        nom = st.text_input("Nom du client")
        date_arr = st.date_input("Date d'arrivée")
        date_dep = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.text_input("Prix brut (€)")
        prix_net = st.text_input("Prix net (€)")
        charges = st.text_input("Charges (€)")
        pourcentage = st.text_input("% (%)")
        submit = st.form_submit_button("Ajouter")

        if submit:
            if all([nom, date_arr, date_dep, plateforme, telephone]):
                new_row = {
                    "nom_client": nom,
                    "date_arrivee": pd.to_datetime(date_arr),
                    "date_depart": pd.to_datetime(date_dep),
                    "plateforme": plateforme,
                    "telephone": telephone,
                    "prix_brut": prix_brut,
                    "prix_net": prix_net,
                    "charges": charges,
                    "%": pourcentage
                }
                if st.session_state.df is not None:
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                else:
                    st.session_state.df = pd.DataFrame([new_row])
                st.success("✅ Réservation ajoutée avec succès.")
            else:
                st.error("❌ Tous les champs requis doivent être remplis.")

elif menu == "📨 Journal des SMS":
    st.header("📨 Historique des SMS")
    if sms_journal:
        st.table(pd.DataFrame(sms_journal))
    else:
        st.info("Aucun SMS encore envoyé.")


