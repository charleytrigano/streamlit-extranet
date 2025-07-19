import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta, date
import calendar
import requests
import os

st.set_page_config(page_title="Extranet Réservations", layout="wide")

st.title("🏨 Portail Extranet - Gestion des Réservations")

# Chargement des clés API Free Mobile
FREE_API_KEY = os.getenv("FREE_API_KEY")
FREE_USER_ID = os.getenv("FREE_USER_ID")
NUMEROS_SMS = os.getenv("NUMERO_DESTINATAIRE", "").split(",")

sms_journal = []

# Gestion du fichier de réservation
FILE_PATH = "reservations.xlsx"

@st.cache_data
def charger_donnees(path):
    return pd.read_excel(path)

@st.cache_data
def sauvegarder_donnees(df):
    df.to_excel(FILE_PATH, index=False)

def envoyer_sms(message):
    resultats = []
    for numero in NUMEROS_SMS:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER_ID}&pass={FREE_API_KEY}&msg={message}"
        try:
            r = requests.get(url)
            statut = "✅ Envoyé" if r.status_code == 200 else f"❌ Erreur {r.status_code}"
            resultats.append((numero, statut))
            sms_journal.append({"Numéro": numero, "Statut": statut, "Message": message})
        except Exception as e:
            sms_journal.append({"Numéro": numero, "Statut": "❌ Erreur", "Message": str(e)})
    return resultats

# Interface onglets
onglet = st.sidebar.radio("📁 Navigation", ["📋 Réservations", "📆 Calendrier", "➕ Nouvelle réservation", "📨 Journal des SMS"])

# Chargement ou création fichier
if os.path.exists(FILE_PATH):
    df = charger_donnees(FILE_PATH)
else:
    colonnes = ["nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"]
    df = pd.DataFrame(columns=colonnes)
    sauvegarder_donnees(df)

# Onglet Réservations
if onglet == "📋 Réservations":
    st.subheader("📋 Liste des réservations")
    st.dataframe(df)

    st.subheader("✏️ Modifier une réservation")
    index = st.selectbox("Sélectionner une ligne à modifier", df.index)
    with st.form("modifier_resa"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom", df.loc[index, "nom_client"])
            plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking"], index=0 if df.loc[index, "plateforme"] == "Airbnb" else 1)
            date_arrivee = st.date_input("Date d'arrivée", df.loc[index, "date_arrivee"])
        with col2:
            date_depart = st.date_input("Date de départ", df.loc[index, "date_depart"])
            tel = st.text_input("Téléphone", df.loc[index, "telephone"])
        
        brut = st.text_input("Prix brut", df.loc[index, "prix_brut"])
        net = st.text_input("Prix net", df.loc[index, "prix_net"])
        charges = st.text_input("Charges", df.loc[index, "charges"])
        pourcent = st.text_input("%", df.loc[index, "%"])

        modif = st.form_submit_button("💾 Enregistrer les modifications")

    if modif:
        df.loc[index] = [nom, date_arrivee, date_depart, plateforme, tel, brut, net, charges, pourcent]
        sauvegarder_donnees(df)
        st.success("Modification enregistrée ✅")

# Onglet Nouvelle réservation
elif onglet == "➕ Nouvelle réservation":
    st.subheader("➕ Ajouter une réservation")
    with st.form("new_resa"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom du client")
            plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking"])
            date_arrivee = st.date_input("Date d'arrivée", date.today())
        with col2:
            date_depart = st.date_input("Date de départ", date.today() + timedelta(days=1))
            tel = st.text_input("Téléphone du client")

        brut = st.text_input("Prix brut (€)")
        net = st.text_input("Prix net (€)")
        charges = st.text_input("Charges (€)")
        pourcent = st.text_input("%")

        submit = st.form_submit_button("✅ Ajouter")

    if submit:
        nouvelle = {
            "nom_client": nom,
            "date_arrivee": date_arrivee,
            "date_depart": date_depart,
            "plateforme": plateforme,
            "telephone": tel,
            "prix_brut": brut,
            "prix_net": net,
            "charges": charges,
            "%": pourcent,
        }
        df = pd.concat([df, pd.DataFrame([nouvelle])], ignore_index=True)
        sauvegarder_donnees(df)
        st.success("Réservation ajoutée ✅")

        # SMS automatique
        message = f"Bonjour {nom},\nNous sommes heureux de vous accueillir demain à Nice.\nParking disponible sur place.\nMerci de nous indiquer votre heure d’arrivée.\nBon voyage et à demain !\nAnnick & Charley"
        envoyer_sms(message)

# Onglet Calendrier
elif onglet == "📆 Calendrier":
    st.subheader("📅 Calendrier mensuel")
    mois = st.selectbox("Mois", list(range(1, 13)), index=date.today().month - 1)
    annee = st.selectbox("Année", list(range(date.today().year - 1, date.today().year + 2)), index=1)

    cal = calendar.Calendar()
    mois_affiche = cal.monthdatescalendar(annee, mois)

    data = {}
    for semaine in mois_affiche:
        for jour in semaine:
            cle = jour.strftime("%Y-%m-%d")
            data[cle] = ""

    for _, row in df.iterrows():
        try:
            debut = pd.to_datetime(row["date_arrivee"]).date()
            fin = pd.to_datetime(row["date_depart"]).date()
            nom = row["nom_client"]
            couleur = "🟦" if row["plateforme"] == "Airbnb" else "🟥"

            for jour in pd.date_range(debut, fin - timedelta(days=0)):
                jour_txt = jour.strftime("%Y-%m-%d")
                if jour.month == mois and jour.year == annee:
                    data[jour_txt] += f"{couleur} {nom}\n"
        except Exception as e:
            st.error(f"Erreur dans le calendrier : {e}")

    # Affichage tableau calendrier
    st.write(f"## {calendar.month_name[mois]} {annee}")
    table = pd.DataFrame(index=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"])

    for semaine in mois_affiche:
        ligne = []
        for jour in semaine:
            cle = jour.strftime("%Y-%m-%d")
            contenu = f"{jour.day}\n{data.get(cle, '')}"
            ligne.append(contenu)
        table[semaine[0].isocalendar()[1]] = ligne

    st.dataframe(table, height=500)

# Onglet Journal SMS
elif onglet == "📨 Journal des SMS":
    st.subheader("📨 Historique des SMS envoyés")
    if sms_journal:
        st.dataframe(pd.DataFrame(sms_journal))
    else:
        st.info("Aucun SMS encore envoyé.")


