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
USER_SMS = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUM_ADMIN = "+33617722379"
SMS_URL = "https://smsapi.free-mobile.fr/sendmsg"

# 🔤 Nettoyer accents & caractères spéciaux
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 🧾 PDF multi-ligne sécurisé
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    mots = texte.split()
    ligne = ""
    for mot in mots:
        if pdf.get_string_width(ligne + " " + mot) < largeur_max:
            ligne += " " + mot
        else:
            try:
                pdf.multi_cell(0, 8, ligne.strip())
            except:
                pdf.multi_cell(0, 8, "<ligne non imprimable>")
            ligne = mot
    if ligne:
        try:
            pdf.multi_cell(0, 8, ligne.strip())
        except:
            pdf.multi_cell(0, 8, "<ligne non imprimable>")

# 📥 Chargement fichier Excel
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

# ➕ Nouvelle Réservation
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

# ✏️ Modifier ou Supprimer
def modifier_reservation(df):
    st.subheader("✏️ Modifier / Supprimer")
    df["identifiant"] = df["nom_client"] + " | " + pd.to_datetime(df["date_arrivee"]).dt.strftime('%Y-%m-%d')
    selection = st.selectbox("Choisir une réservation", df["identifiant"])
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
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    with col2:
        annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    nb_jours = calendar.monthrange(int(annee), int(mois_index))[1]
    jours = [date(int(annee), int(mois_index), i+1) for i in range(nb_jours)]
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
    for semaine in calendar.monthcalendar(int(annee), int(mois_index)):
        ligne = []
        for jour in semaine:
            if jour == 0:
                ligne.append("")
            else:
                jour_date = date(int(annee), int(mois_index), jour)
                contenu = f"{jour}\n" + "\n".join(planning[jour_date])
                ligne.append(contenu)
        table.append(ligne)
    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 📋 Liste des clients
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        data["prix brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        data["prix net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        st.dataframe(data[["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix brut/nuit", "prix net/nuit"]])
        total_row = {
            "nom_client": "TOTAL",
            "nuitees": int(data["nuitees"].sum()),
            "prix_brut": round(data["prix_brut"].sum(), 2),
            "prix_net": round(data["prix_net"].sum(), 2),
            "charges": round(data["charges"].sum(), 2),
        }
        st.write("Total nuitées :", total_row["nuitees"])
        st.write("Total brut :", total_row["prix_brut"])
        st.write("Total net :", total_row["prix_net"])
        st.write("Total charges :", total_row["charges"])
    else:
        st.info("Aucune donnée pour cette période.")

# 📩 Envoi SMS personnalisé
def envoyer_sms(numero, message):
    params = {"user": USER_SMS, "pass": API_KEY, "msg": message}
    response = requests.get(SMS_URL, params=params)
    return response.status_code == 200

# 🕓 Notifications à venir
def sms_a_envoyer(df):
    st.subheader("📩 SMS à envoyer (J-1)")
    demain = date.today() + timedelta(days=1)
    a_notifier = df[df["date_arrivee"] == demain]
    if not a_notifier.empty:
        for _, row in a_notifier.iterrows():
            message = f"VILLA TOBIAS - {row['plateforme']}\nBonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}. Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. Nous vous rappelons qu’un parking est à votre disposition sur place. À demain."
            if st.button(f"Envoyer SMS à {row['nom_client']}"):
                succes = envoyer_sms(NUM_ADMIN, message)
                if succes:
                    st.success("SMS envoyé avec succès ✅")
                    historique = pd.DataFrame([{
                        "nom_client": row["nom_client"],
                        "date_arrivee": row["date_arrivee"],
                        "envoye_le": date.today(),
                        "contenu": message
                    }])
                    if os.path.exists(HISTORIQUE_SMS):
                        histo = pd.read_csv(HISTORIQUE_SMS)
                        historique = pd.concat([histo, historique], ignore_index=True)
                    historique.to_csv(HISTORIQUE_SMS, index=False)
                else:
                    st.error("Erreur lors de l'envoi")

# ▶️ Lancement
def main():
    st.set_page_config(layout="wide")
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📋 Liste Clients", "📩 SMS"])
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
    elif onglet == "📩 SMS":
        sms_a_envoyer(df)

if __name__ == "__main__":
    main()