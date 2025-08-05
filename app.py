import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import os
import requests

FICHIER = "reservations.xlsx"
FICHIER_SMS = "historique_sms.csv"

# 🔤 Nettoyer accents & caractères spéciaux
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 📤 Envoi du SMS via Free Mobile
def envoyer_sms(numero, message):
    api_user = "12026027"
    api_key = "MF7Qjs3C8KxKHz"
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={api_user}&pass={api_key}&msg={message}"
    response = requests.get(url)
    return response.status_code == 200

# ✅ Historique SMS
def enregistrer_sms(nom, numero, message, date_envoi):
    historique = pd.DataFrame([[nom, numero, message, date_envoi]],
                              columns=["Nom", "Téléphone", "Message", "Date d'envoi"])
    if os.path.exists(FICHIER_SMS):
        ancien = pd.read_csv(FICHIER_SMS)
        historique = pd.concat([ancien, historique], ignore_index=True)
    historique.to_csv(FICHIER_SMS, index=False)

# 🧾 PDF multi lignes
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        mots = texte.split()
        ligne = ""
        for mot in mots:
            test = ligne + " " + mot
            if pdf.get_string_width(test) > largeur_max:
                pdf.multi_cell(0, 8, ligne)
                ligne = mot
            else:
                ligne = test
        if ligne:
            pdf.multi_cell(0, 8, ligne)
    except Exception:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

# 📥 Chargement fichier Excel
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

# ➕ Ajouter réservation
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
                "%": round((prix_brut - prix_net) / prix_brut * 100, 2) if prix_brut else 0,
                "nuitees": (depart - arrivee).days,
                "annee": arrivee.year,
                "mois": arrivee.month
            }
            df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation enregistrée")
    return df

# ✏️ Modifier ou supprimer
def modifier_reservation(df):
    st.subheader("✏️ Modifier / Supprimer")
    df["identifiant"] = df["nom_client"] + " | " + pd.to_datetime(df["date_arrivee"]).dt.strftime('%Y-%m-%d')
    selection = st.selectbox("Choisissez une réservation", df["identifiant"])
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
    col1, col2 = st.columns(2)
    with col1:
        annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    with col2:
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    mois_index = list(calendar.month_name).index(mois_nom)
    nb_jours = calendar.monthrange(int(annee), mois_index)[1]
    jours = [date(int(annee), mois_index, i+1) for i in range(nb_jours)]
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
    for semaine in calendar.monthcalendar(int(annee), mois_index):
        ligne = []
        for jour in semaine:
            if jour == 0:
                ligne.append("")
            else:
                jour_date = date(int(annee), mois_index, jour)
                contenu = f"{jour}\n" + "\n".join(planning[jour_date])
                ligne.append(contenu)
        table.append(ligne)
    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 📋 Liste clients
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()), key="liste_annee")
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()), key="liste_mois")
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == int(mois)]
    if not data.empty:
        data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit"]
        total = data[colonnes[4:]].sum(numeric_only=True)
        total["nom_client"] = "Total"
        total["plateforme"] = ""
        total["date_arrivee"] = ""
        total["date_depart"] = ""
        data_affichee = pd.concat([data[colonnes], pd.DataFrame([total])], ignore_index=True)
        st.dataframe(data_affichee)
        # Bouton SMS
        if st.button("📩 Envoyer SMS aux clients arrivant demain"):
            demain = date.today() + timedelta(days=1)
            a_notifier = df[df["date_arrivee"] == demain]
            for _, row in a_notifier.iterrows():
                message = f"VILLA TOBIAS - {row['plateforme']}\nBonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}. Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. Un parking est disponible sur place. À demain !"
                if envoyer_sms(row["telephone"], message):
                    enregistrer_sms(row["nom_client"], row["telephone"], message, str(date.today()))
            st.success("📲 SMS envoyés aux clients de demain.")
    else:
        st.info("Aucune donnée disponible pour cette période.")

# 📜 Historique des SMS
def afficher_historique_sms():
    st.subheader("📜 Historique des SMS envoyés")
    if os.path.exists(FICHIER_SMS):
        df_sms = pd.read_csv(FICHIER_SMS)
        st.dataframe(df_sms)
    else:
        st.info("Aucun SMS encore envoyé.")

# ▶️ Lancement
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📋 Liste Clients", "📜 Historique SMS"])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📋 Liste Clients":
        liste_clients(df)
    elif onglet == "📜 Historique SMS":
        afficher_historique_sms()

if __name__ == "__main__":
    main()