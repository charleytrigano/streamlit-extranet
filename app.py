import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import requests
import csv
import unicodedata
from io import BytesIO

# Fichier Excel et CSV
FICHIER = "reservations.xlsx"
HISTORIQUE_SMS = "historique_sms.csv"

# API Free
USER = "VotreIdentifiant"
API_KEY = "VotreCléAPI"
PHONE_NUMBER = "+33617722379"

# Nettoyer accents et caractères spéciaux
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# Envoi du SMS
def envoyer_sms(message, numero):
    url = "https://smsapi.free-mobile.fr/sendmsg"
    params = {
        "user": USER,
        "pass": API_KEY,
        "msg": message,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        # Enregistrer l'historique dans le CSV
        with open(HISTORIQUE_SMS, mode="a", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), numero, message])
        return True
    else:
        return False

# Charger les données du fichier Excel
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce")
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce")
    df["charges"] = df["prix_brut"] - df["prix_net"]
    df["%"] = (df["charges"] / df["prix_brut"] * 100).round(2)
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    df["annee"] = df["date_arrivee"].dt.year
    df["mois"] = df["date_arrivee"].dt.month
    return df

# Interface pour envoyer des SMS
def envoyer_sms_clients(df):
    st.subheader("✉️ Envoyer un SMS aux clients")
    for index, row in df.iterrows():
        message = f"VILLA TOBIAS - {row['plateforme']}\nBonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee'].strftime('%d/%m/%Y')} au {row['date_depart'].strftime('%d/%m/%Y')}. Afin de vous accueillir merci de nous confirmer votre heure d'arrivée. Nous vous rappelons qu'un parking est à votre disposition sur place. A demain."
        numero = row['telephone']
        if st.button(f"Envoyer SMS à {row['nom_client']}"):
            if envoyer_sms(message, numero):
                st.success(f"SMS envoyé à {row['nom_client']} avec succès!")
            else:
                st.error(f"Erreur lors de l'envoi du SMS à {row['nom_client']}.")

# Affichage de l'historique des SMS envoyés
def afficher_historique_sms():
    st.subheader("📜 Historique des SMS")
    try:
        historique_df = pd.read_csv(HISTORIQUE_SMS, names=["Date", "Numéro", "Message"])
        st.dataframe(historique_df)
    except FileNotFoundError:
        st.info("Aucun historique d'envoi de SMS trouvé.")

# Fonction pour télécharger l'historique des SMS
def telecharger_historique_sms():
    try:
        historique_df = pd.read_csv(HISTORIQUE_SMS, names=["Date", "Numéro", "Message"])
        csv_buffer = BytesIO()
        historique_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        st.download_button(
            label="Télécharger l'historique des SMS",
            data=csv_buffer,
            file_name="historique_sms.csv",
            mime="text/csv",
        )
    except FileNotFoundError:
        st.info("Aucun historique d'envoi de SMS trouvé.")

# Affichage du calendrier
def afficher_calendrier(df):
    st.subheader("📅 Calendrier des réservations")
    col1, col2 = st.columns(2)
    with col1:
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    with col2:
        annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    nb_jours = calendar.monthrange(annee, mois_index)[1]
    jours = [datetime(annee, mois_index, i+1) for i in range(nb_jours)]
    planning = {jour: [] for jour in jours}
    couleurs = {"Booking": "🟦", "Airbnb": "🟩", "Autre": "🟧"}
    for _, row in df.iterrows():
        debut = row["date_arrivee"].date()
        fin = row["date_depart"].date()
        for jour in jours:
            if debut <= jour < fin:
                icone = couleurs.get(row["plateforme"], "⬜")
                planning[jour].append(f"{icone} {row['nom_client']}")
    table = []
    for semaine in calendar.monthcalendar(annee, mois_index):
        ligne = []
        for jour in semaine:
            if jour == 0:
                ligne.append("")
            else:
                jour_date = datetime(annee, mois_index, jour)
                contenu = f"{jour}\n" + "\n".join(planning[jour_date])
                ligne.append(contenu)
        table.append(ligne)
    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# Fonction principale
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📲 SMS"])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)
    elif onglet == "📲 SMS":
        envoyer_sms_clients(df)
        afficher_historique_sms()
        telecharger_historique_sms()

if __name__ == "__main__":
    main()