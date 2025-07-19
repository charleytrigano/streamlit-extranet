import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta, datetime as dt
import requests
import calendar
import openpyxl

# Configuration
st.set_page_config(page_title="Extranet Airbnb / Booking", layout="wide")

# ------------------ VARIABLES ------------------
FICHIER_RESERVATIONS = "reservations.xlsx"
FREE_API_KEYS = {
    "+33617722379": "MF7Qjs3C8KxKHz",
    "+33611772793": "1Pat6vSRCLiSXl"
}
FREE_USER_ID = "12026027"
JOURNAL_SMS = []

# ------------------ CHARGER RESERVATIONS ------------------
def charger_reservations():
    try:
        df = pd.read_excel(FICHIER_RESERVATIONS)
        for col in ["date_arrivee", "date_depart"]:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()

# ------------------ ENREGISTRER RESERVATIONS ------------------
def enregistrer_reservations(df):
    try:
        df.to_excel(FICHIER_RESERVATIONS, index=False)
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")

# ------------------ ENVOI SMS ------------------
def envoyer_sms(message):
    for numero, cle in FREE_API_KEYS.items():
        try:
            url = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER_ID}&pass={cle}&msg={requests.utils.quote(message)}"
            response = requests.get(url)
            if response.status_code == 200:
                JOURNAL_SMS.append((numero, message, dt.now().strftime("%Y-%m-%d %H:%M:%S")))
            else:
                JOURNAL_SMS.append((numero, "❌ Échec", dt.now().strftime("%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            st.warning(f"Erreur SMS à {numero} : {e}")

# ------------------ AJOUT RESERVATION ------------------
def ajouter_reservation(df):
    with st.form("ajouter_resa", clear_on_submit=True):
        st.subheader("➕ Nouvelle réservation")
        col1, col2, col3 = st.columns(3)
        with col1:
            nom_client = st.text_input("Nom du client")
            plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking"])
            telephone = st.text_input("Téléphone")
        with col2:
            date_arrivee = st.date_input("Date d'arrivée", dt.today())
            date_depart = st.date_input("Date de départ", dt.today() + timedelta(days=1))
        with col3:
            prix_brut = st.text_input("Prix brut")
            prix_net = st.text_input("Prix net")
            charges = st.text_input("Charges")
            pourcentage = st.text_input("%")

        submit = st.form_submit_button("✅ Enregistrer")
        if submit:
            nouvelle = {
                "nom_client": nom_client,
                "date_arrivee": date_arrivee,
                "date_depart": date_depart,
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcentage
            }
            df = pd.concat([df, pd.DataFrame([nouvelle])], ignore_index=True)
            enregistrer_reservations(df)
            st.success("Réservation ajoutée !")
            envoyer_sms(
                f"Bonjour {nom_client}, nous sommes heureux de vous accueillir demain à Nice.\n"
                "Un emplacement de parking est à votre disposition sur place. Merci de nous indiquer votre heure d’arrivée.\n"
                "Bon voyage et à demain !\nAnnick & Charley"
            )

# ------------------ CALENDRIER ------------------
def afficher_calendrier(df):
    st.subheader("📅 Calendrier des réservations")
    today = dt.today()
    col1, col2 = st.columns([1, 1])
    with col1:
        mois = st.selectbox("Mois", list(calendar.month_name)[1:], index=today.month - 1)
    with col2:
        annee = st.selectbox("Année", list(range(today.year, today.year + 2)), index=0)

    mois_index = list(calendar.month_name).index(mois)
    cal = calendar.Calendar()
    jours = list(cal.itermonthdates(annee, mois_index))

    df_periode = df[
        (df["date_arrivee"].dt.month == mois_index) & 
        (df["date_arrivee"].dt.year == annee)
    ]

    grille = {}
    for jour in jours:
        grille[jour] = []

    for _, row in df.iterrows():
        arrivee = row["date_arrivee"]
        depart = row["date_depart"]
        if pd.notna(arrivee) and pd.notna(depart):
            for jour in pd.date_range(arrivee, depart - timedelta(days=0)).date:
                if jour in grille:
                    grille[jour].append(f"{row['nom_client']} ({row['plateforme']})")

    for semaine in calendar.monthcalendar(annee, mois_index):
        cols = st.columns(7)
        for i, jour in enumerate(semaine):
            if jour == 0:
                cols[i].markdown(" ")
            else:
                date = datetime.date(annee, mois_index, jour)
                contenu = "\n".join(grille.get(date, []))
                couleur = "#DFF0D8" if contenu else "#F9F9F9"
                cols[i].markdown(
                    f"<div style='background-color:{couleur}; padding:5px; border-radius:5px;'>"
                    f"<strong>{jour}</strong><br>{contenu}</div>", unsafe_allow_html=True
                )

# ------------------ TABLEAU RESERVATIONS ------------------
def afficher_tableau(df):
    st.subheader("📋 Tableau des réservations")
    df_affichage = df.copy()
    for col in df_affichage.columns:
        if df_affichage[col].dtype == object:
            df_affichage[col] = df_affichage[col].astype(str)
    st.dataframe(df_affichage, use_container_width=True)

# ------------------ JOURNAL SMS ------------------
def afficher_journal_sms():
    st.subheader("📨 Journal des SMS envoyés")
    if JOURNAL_SMS:
        st.table(pd.DataFrame(JOURNAL_SMS, columns=["Téléphone", "Message", "Date/Heure"]))
    else:
        st.info("Aucun SMS envoyé.")

# ------------------ APPLICATION ------------------
def main():
    st.title("🏨 Portail Extranet Streamlit")
    onglet = st.sidebar.radio("Navigation", ["📥 Fichier", "📅 Calendrier", "📝 Nouvelle réservation", "📨 Journal SMS"])
    df = charger_reservations()

    if onglet == "📥 Fichier":
        afficher_tableau(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📝 Nouvelle réservation":
        ajouter_reservation(df)
    elif onglet == "📨 Journal SMS":
        afficher_journal_sms()

main()
