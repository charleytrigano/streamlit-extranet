import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import requests
import os

FICHIER = "reservations.xlsx"
HISTORIQUE_SMS = "historique_sms.csv"
USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUMERO_ADMIN = "+33617722379"
URL_SMS = "https://smsapi.free-mobile.fr/sendmsg"

# 🔤 Nettoyer accents & caractères spéciaux
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# ✅ Lecture des données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

# 💬 Fonction d’envoi de SMS
def envoyer_sms(numero, message):
    try:
        params = {"user": USER, "pass": API_KEY, "msg": message}
        requests.get(URL_SMS, params=params, timeout=10)
    except Exception as e:
        st.error(f"Erreur SMS : {e}")

# 📜 Sauvegarder historique SMS
def enregistrer_sms(client, numero, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ligne = pd.DataFrame([{
        "date_envoi": now,
        "nom_client": client,
        "numero": numero,
        "message": message
    }])
    if os.path.exists(HISTORIQUE_SMS):
        ligne.to_csv(HISTORIQUE_SMS, mode="a", header=False, index=False)
    else:
        ligne.to_csv(HISTORIQUE_SMS, index=False)

# 📤 Notification automatique J-1
def notifier_arrivees_prochaines(df):
    demain = date.today() + timedelta(days=1)
    df_notif = df[df["date_arrivee"] == demain]
    for _, row in df_notif.iterrows():
        message = f"""VILLA TOBIAS - {row['plateforme']}
Bonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}.
Afin de vous accueillir merci de nous confirmer votre heure d’arrivée.
Nous vous rappelons qu'un parking est à votre disposition sur place. À demain."""
        envoyer_sms(NUMERO_ADMIN, message)
        enregistrer_sms(row["nom_client"], NUMERO_ADMIN, message)

# ➕ Nouvelle réservation
def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajout"):
        nom = st.text_input("Nom")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        tel = st.text_input("Téléphone")
        arrivee = st.date_input("Date arrivée")
        depart = st.date_input("Date départ", min_value=arrivee + timedelta(days=1))
        prix_brut = st.number_input("Prix brut", min_value=0.0)
        prix_net = st.number_input("Prix net", min_value=0.0, max_value=prix_brut)
        submit = st.form_submit_button("Enregistrer")
        if submit:
            ligne = {
                "nom_client": nom,
                "plateforme": plateforme,
                "telephone": tel,
                "date_arrivee": arrivee,
                "date_depart": depart,
                "prix_brut": round(prix_brut, 2),
                "prix_net": round(prix_net, 2),
                "charges": round(prix_brut - prix_net, 2),
                "%": round(((prix_brut - prix_net) / prix_brut) * 100, 2) if prix_brut else 0,
                "nuitees": (depart - arrivee).days,
                "annee": arrivee.year,
                "mois": arrivee.month
            }
            df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation enregistrée")
    return df

# ✏️ Modifier / Supprimer
def modifier_reservation(df):
    st.subheader("✏️ Modifier / Supprimer")
    df["identifiant"] = df["nom_client"] + " | " + df["date_arrivee"].astype(str)
    selection = st.selectbox("Choisir réservation", df["identifiant"])
    i = df[df["identifiant"] == selection].index[0]
    with st.form("modif"):
        nom = st.text_input("Nom", df.at[i, "nom_client"])
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(df.at[i, "plateforme"]))
        tel = st.text_input("Téléphone", df.at[i, "telephone"])
        arrivee = st.date_input("Arrivée", df.at[i, "date_arrivee"])
        depart = st.date_input("Départ", df.at[i, "date_depart"])
        brut = st.number_input("Prix brut", value=float(df.at[i, "prix_brut"]))
        net = st.number_input("Prix net", value=float(df.at[i, "prix_net"]))
        submit = st.form_submit_button("Modifier")
        delete = st.form_submit_button("Supprimer")
        if submit:
            df.at[i, "nom_client"] = nom
            df.at[i, "plateforme"] = plateforme
            df.at[i, "telephone"] = tel
            df.at[i, "date_arrivee"] = arrivee
            df.at[i, "date_depart"] = depart
            df.at[i, "prix_brut"] = round(brut, 2)
            df.at[i, "prix_net"] = round(net, 2)
            df.at[i, "charges"] = round(brut - net, 2)
            df.at[i, "%"] = round((brut - net) / brut * 100, 2) if brut else 0
            df.at[i, "nuitees"] = (depart - arrivee).days
            df.at[i, "annee"] = arrivee.year
            df.at[i, "mois"] = arrivee.month
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation modifiée")
        if delete:
            df.drop(index=i, inplace=True)
            df.to_excel(FICHIER, index=False)
            st.warning("🗑 Réservation supprimée")
    return df

# 📅 Calendrier
def afficher_calendrier(df):
    st.subheader("📅 Calendrier")
    mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    nb_jours = calendar.monthrange(annee, mois_index)[1]
    jours = [date(annee, mois_index, i+1) for i in range(nb_jours)]
    planning = {jour: [] for jour in jours}
    couleurs = {"Booking": "🟦", "Airbnb": "🟩", "Autre": "🟧"}
    for _, row in df.iterrows():
        debut = row["date_arrivee"]
        fin = row["date_depart"]
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
                jour_date = date(annee, mois_index, jour)
                contenu = f"{jour}\n" + "\n".join(planning[jour_date])
                ligne.append(contenu)
        table.append(ligne)
    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 📋 Liste des clients
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()), key="annee_liste")
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()), key="mois_liste")
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit"]
        total = data[colonnes[4:]].sum(numeric_only=True).to_frame().T
        total.insert(0, "nom_client", "TOTAL")
        total.insert(1, "plateforme", "")
        total.insert(2, "date_arrivee", "")
        total.insert(3, "date_depart", "")
        df_final = pd.concat([data[colonnes], total], ignore_index=True)
        st.dataframe(df_final)
        # SMS manuel
        st.markdown("### 📲 Envoyer un SMS à un client")
        choix = st.selectbox("Choisissez un client", data["nom_client"].unique())
        client = data[data["nom_client"] == choix].iloc[0]
        msg = f"""VILLA TOBIAS - {client['plateforme']}
Bonjour {client['nom_client']}. Votre séjour est prévu du {client['date_arrivee']} au {client['date_depart']}.
Afin de vous accueillir merci de nous confirmer votre heure d’arrivée.
Nous vous rappelons qu'un parking est à votre disposition sur place. À demain."""
        if st.button("📤 Envoyer SMS maintenant"):
            envoyer_sms(NUMERO_ADMIN, msg)
            enregistrer_sms(client["nom_client"], NUMERO_ADMIN, msg)
            st.success("SMS envoyé")
    else:
        st.info("Aucune donnée")

# 🕘 Historique des SMS
def historique_sms():
    st.subheader("🕘 Historique des SMS")
    if os.path.exists(HISTORIQUE_SMS):
        histo = pd.read_csv(HISTORIQUE_SMS)
        st.dataframe(histo)
    else:
        st.info("Aucun SMS envoyé pour le moment.")

# ▶️ Interface principale
def main():
    df = charger_donnees()
    notifier_arrivees_prochaines(df)
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📋 Liste Clients", "🕘 Historique SMS"])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df)
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📋 Liste Clients":
        liste_clients(df)
    elif onglet == "🕘 Historique SMS":
        historique_sms()
    elif onglet == "📊 Rapport":
        st.info("Rapport mensuel désactivé dans cette version simplifiée. Utilisez Liste Clients pour le suivi.")

if __name__ == "__main__":
    main()