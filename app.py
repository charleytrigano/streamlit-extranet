import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import calendar

st.set_page_config(page_title="Extranet Réservations", layout="wide")

# ------------------------- CONFIGURATION -------------------------
FREE_SMS_API_KEYS = [
    {"user": "12026027", "key": "1Pat6vSRCLiSXl", "tel": "+33611772793"},
    {"user": "12026027", "key": "MF7Qjs3C8KxKHz", "tel": "+33617722379"}
]

FICHIER_EXCEL = "reservations.xlsx"

# ------------------------- FONCTIONS UTILES -------------------------
def charger_donnees():
    try:
        return pd.read_excel(FICHIER_EXCEL)
    except Exception:
        return pd.DataFrame(columns=[
            "nom_client", "date_arrivee", "date_depart", "plateforme",
            "telephone", "prix_brut", "prix_net", "charges", "%"
        ])

def sauvegarder_donnees(df):
    df.to_excel(FICHIER_EXCEL, index=False)

def envoyer_sms(message):
    for contact in FREE_SMS_API_KEYS:
        payload = {
            "user": contact["user"],
            "pass": contact["key"],
            "msg": message
        }
        try:
            requests.get("https://smsapi.free-mobile.fr/sendmsg", params=payload)
        except Exception as e:
            st.warning(f"Erreur SMS vers {contact['tel']} : {e}")

def verifier_sms_a_envoyer(df):
    aujourd_hui = datetime.now().date()
    demain = aujourd_hui + timedelta(days=1)

    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df_demain = df[df["date_arrivee"].dt.normalize() == pd.to_datetime(demain)]

    journal_sms = []

    for _, row in df_demain.iterrows():
        msg = (
            f"Bonjour {row['nom_client']},\n"
            f"Nous sommes heureux de vous accueillir demain à Nice.\n"
            f"Un emplacement de parking est à votre disposition sur place.\n"
            f"Merci de nous indiquer votre heure d'arrivée.\n"
            f"Bon voyage et à demain !\n"
            f"Annick & Charley"
        )
        envoyer_sms(msg)
        journal_sms.append((row['nom_client'], row['date_arrivee'].date(), msg))

    return journal_sms

# ------------------------- CALENDRIER -------------------------
def afficher_calendrier(df):
    st.subheader("📅 Calendrier mensuel")

    mois_selectionne = st.selectbox("Mois :", list(calendar.month_name)[1:], index=datetime.today().month - 1)
    annee_selectionnee = st.number_input("Année :", value=datetime.today().year, format="%d")

    mois_index = list(calendar.month_name).index(mois_selectionne)

    # S'assurer que les dates sont bien au format datetime
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

    # Créer tableau vide du mois
    cal = calendar.Calendar(firstweekday=0)
    jours_mois = list(cal.itermonthdates(annee_selectionnee, mois_index))
    cases = {jour: [] for jour in jours_mois if jour.month == mois_index}

    for _, row in df.iterrows():
        try:
            arrivee = row["date_arrivee"].date()
            depart = row["date_depart"].date()
            for jour in pd.date_range(arrivee, depart - timedelta(days=1)).date:
                if jour in cases:
                    txt = f"{row['nom_client']} ({row['plateforme']})"
                    cases[jour].append(txt)
        except:
            continue

    # Affichage
    jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    st.markdown("### ")

    cols = st.columns(7)
    for i, j in enumerate(jours_semaine):
        cols[i].markdown(f"**{j}**")

    cal_rows = [jours_mois[i:i+7] for i in range(0, len(jours_mois), 7)]

    for semaine in cal_rows:
        row_cols = st.columns(7)
        for i, jour in enumerate(semaine):
            if jour.month == mois_index:
                txt = f"**{jour.day}**"
                for client in cases.get(jour, []):
                    txt += f"<br/><small>{client}</small>"
                row_cols[i].markdown(txt, unsafe_allow_html=True)
            else:
                row_cols[i].markdown("")

# ------------------------- INTERFACE PRINCIPALE -------------------------
def main():
    st.title("🏨 Portail Extranet - Réservations")
    onglet = st.sidebar.radio("Navigation", ["Tableau des réservations", "Ajouter une réservation", "Calendrier"])

    df = charger_donnees()

    if onglet == "Tableau des réservations":
        st.subheader("📋 Réservations en cours")
        st.dataframe(df)

        st.markdown("### 📩 Envoi de SMS")
        if st.button("Envoyer les SMS aux arrivées de demain"):
            journal = verifier_sms_a_envoyer(df)
            if journal:
                st.success("📨 SMS envoyés :")
                for log in journal:
                    st.text(f"{log[0]} - {log[1]}")
            else:
                st.info("Aucun client attendu demain.")

    elif onglet == "Ajouter une réservation":
        st.subheader("➕ Ajouter une nouvelle réservation")

        with st.form("formulaire"):
            nom = st.text_input("Nom du client")
            plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
            tel = st.text_input("Téléphone")
            arrivee = st.date_input("Date d'arrivée")
            depart = st.date_input("Date de départ", min_value=arrivee)
            prix_brut = st.text_input("Prix brut")
            prix_net = st.text_input("Prix net")
            charges = st.text_input("Charges")
            pourcent = st.text_input("%")

            submit = st.form_submit_button("Enregistrer")

        if submit:
            nouvelle = pd.DataFrame([{
                "nom_client": nom,
                "plateforme": plateforme,
                "telephone": tel,
                "date_arrivee": arrivee,
                "date_depart": depart,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcent
            }])
            df = pd.concat([df, nouvelle], ignore_index=True)
            sauvegarder_donnees(df)
            st.success("✅ Réservation ajoutée avec succès.")

    elif onglet == "Calendrier":
        afficher_calendrier(df)

if __name__ == "__main__":
    main()

