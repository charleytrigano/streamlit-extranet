import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from io import BytesIO
import unicodedata
import requests
import os

FICHIER = "reservations.xlsx"
HISTORIQUE_SMS = "historique_sms.csv"

# Identifiants API Free
NUMERO_USER = "12026027"
CLE_API = "MF7Qjs3C8KxKHz"
NUMERO_ADMIN = "+33617722379"

# Nettoyage texte
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# Chargement des données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

# Fonction SMS via Free
def envoyer_sms(destinataire, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg"
    params = {
        "user": NUMERO_USER,
        "pass": CLE_API,
        "msg": message
    }
    response = requests.get(url, params=params)
    return response.status_code == 200

# Message personnalisé
def generer_message(row):
    return (
        f"VILLA TOBIAS - {row['plateforme']}\n"
        f"Bonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}. "
        f"Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. "
        f"Nous vous rappelons qu’un parking est à votre disposition sur place. À demain."
    )

# Historique SMS
def enregistrer_sms(row, message):
    historique = pd.DataFrame([{
        "date_envoi": date.today(),
        "nom_client": row["nom_client"],
        "telephone": row["telephone"],
        "date_arrivee": row["date_arrivee"],
        "message": message
    }])
    if os.path.exists(HISTORIQUE_SMS):
        historique.to_csv(HISTORIQUE_SMS, mode='a', index=False, header=False)
    else:
        historique.to_csv(HISTORIQUE_SMS, index=False)

# Onglet: Liste des clients
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()), key="annee_liste")
    mois = st.selectbox("Mois", ["Tous"] + list(range(1, 13)), key="mois_liste")
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]

    data["prix_moyen_brut"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    data["prix_moyen_net"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)

    colonnes = ["nom_client", "plateforme", "telephone", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_moyen_brut", "prix_moyen_net"]
    st.dataframe(data[colonnes])

    st.markdown("### 📤 Exporter en Excel")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data[colonnes].to_excel(writer, index=False)
    buffer.seek(0)
    st.download_button("📥 Télécharger", buffer, file_name="liste_clients.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("### 📲 Envoyer un SMS")
    for i, row in data.iterrows():
        message = generer_message(row)
        if st.button(f"Envoyer SMS à {row['nom_client']} ({row['telephone']})", key=f"sms_{i}"):
            success = envoyer_sms(row["telephone"], message)
            enregistrer_sms(row, message)
            if success:
                st.success("SMS envoyé ✅")
            else:
                st.error("Échec de l'envoi ❌")

# Onglet Historique
def historique_sms():
    st.subheader("📜 Historique des SMS")
    if os.path.exists(HISTORIQUE_SMS):
        hist = pd.read_csv(HISTORIQUE_SMS)
        st.dataframe(hist)
    else:
        st.info("Aucun SMS envoyé pour le moment.")

# Envoi automatique (veille)
def envoi_automatique(df):
    demain = date.today() + timedelta(days=1)
    for _, row in df.iterrows():
        if row["date_arrivee"] == demain:
            message = generer_message(row)
            envoyer_sms(row["telephone"], message)
            enregistrer_sms(row, message)

# Onglets supplémentaires (Ajouter, Modifier, etc.) à réintégrer ici selon vos besoins...

# Lancement App
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Liste des clients", "📜 Historique SMS"])
    if onglet == "📋 Liste des clients":
        liste_clients(df)
    elif onglet == "📜 Historique SMS":
        historique_sms()

    # Activer l'envoi automatique en tâche de fond (peut être conditionné à un bouton)
    envoi_automatique(df)

if __name__ == "__main__":
    main()