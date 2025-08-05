# app.py

import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import os
import requests

FICHIER = "reservations.xlsx"
SMS_HISTORIQUE = "historique_sms.csv"

# 🔧 Paramètres Free API
USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUM_PROPRIO = "+33617722379"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce")
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce")
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    df["prix_brut_nuit"] = (df["prix_brut"] / df["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["prix_net_nuit"] = (df["prix_net"] / df["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    return df

def envoyer_sms(telephone, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg"
    payload = {
        "user": USER,
        "pass": API_KEY,
        "msg": message
    }
    response = requests.get(url, params=payload)
    return response.status_code == 200

def logger_sms(nom_client, telephone, message):
    log = pd.DataFrame([{
        "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "client": nom_client,
        "telephone": telephone,
        "message": message
    }])
    if os.path.exists(SMS_HISTORIQUE):
        ancien = pd.read_csv(SMS_HISTORIQUE)
        log = pd.concat([ancien, log], ignore_index=True)
    log.to_csv(SMS_HISTORIQUE, index=False)

def notifier_arrivees_prochaines(df):
    st.subheader("📩 SMS à envoyer")
    demain = date.today() + timedelta(days=1)
    df_sms = df[df["date_arrivee"] == demain]
    if df_sms.empty:
        st.info("Aucun client prévu demain.")
    else:
        for _, row in df_sms.iterrows():
            message = f"VILLA TOBIAS - {row['plateforme']}\nBonjour {row['nom_client']}. Votre sejour est prevu du {row['date_arrivee']} au {row['date_depart']}. Afin de vous accueillir merci de nous confirmer votre heure d arrivee. Nous vous rappelons qu'un parking est a votre disposition sur place. A demain"
            st.markdown(f"**{row['nom_client']}** ({row['plateforme']}) - {row['date_arrivee']} ➡ {row['date_depart']}")
            if st.button(f"Envoyer SMS à {row['nom_client']}", key=row["nom_client"]):
                ok = envoyer_sms(NUM_PROPRIO, message)
                if ok:
                    st.success("✅ SMS envoyé")
                    logger_sms(row['nom_client'], NUM_PROPRIO, message)
                else:
                    st.error("❌ Échec envoi SMS")

def historique_sms():
    st.subheader("📜 Historique SMS envoyés")
    if os.path.exists(SMS_HISTORIQUE):
        log = pd.read_csv(SMS_HISTORIQUE)
        st.dataframe(log)
    else:
        st.info("Aucun SMS envoyé pour l’instant.")

def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajout"):
        nom = st.text_input("Nom")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        tel = st.text_input("Téléphone")
        arrivee = st.date_input("Date arrivée")
        depart = st.date_input("Date départ", min_value=arrivee + timedelta(days=1))
        prix_brut = st.number_input("Prix brut", min_value=0.0, step=1.0)
        prix_net = st.number_input("Prix net", min_value=0.0, max_value=prix_brut, step=1.0)
        submit = st.form_submit_button("Enregistrer")
        if submit:
            ligne = {
                "nom_client": nom,
                "plateforme": plateforme,
                "telephone": tel,
                "date_arrivee": arrivee,
                "date_depart": depart,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
            }
            df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation enregistrée")
    return charger_donnees()

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
            df.at[i, "prix_brut"] = brut
            df.at[i, "prix_net"] = net
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation modifiée")
        if delete:
            df.drop(index=i, inplace=True)
            df.to_excel(FICHIER, index=False)
            st.warning("🗑 Réservation supprimée")
    return charger_donnees()

def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == int(mois)]
    if not data.empty:
        reg = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum", "prix_net": "sum", "charges": "sum", "%": "mean", "nuitees": "sum"
        }).reset_index()
        reg["prix_moyen_brut"] = (reg["prix_brut"] / reg["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        reg["prix_moyen_net"] = (reg["prix_net"] / reg["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        st.dataframe(reg)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune donnée pour cette période.")

def afficher_calendrier(df):
    st.subheader("📅 Calendrier")
    col1, col2 = st.columns(2)
    with col1:
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    with col2:
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

def liste_clients(df):
    st.subheader("📄 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == int(mois)]
    if not data.empty:
        total = pd.DataFrame(data[[
            "prix_brut", "prix_net", "charges", "nuitees", "prix_brut_nuit", "prix_net_nuit", "%"
        ]].sum()).T
        total["nom_client"] = "TOTAL"
        colonnes = ["nom_client", "date_arrivee", "date_depart", "nuitees", "plateforme", "prix_brut", "prix_net", "charges", "%", "prix_brut_nuit", "prix_net_nuit"]
        data = data[colonnes]
        data = pd.concat([data, total[colonnes]], ignore_index=True)
        st.dataframe(data)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            data.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"liste_clients_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucun client trouvé.")

def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📄 Liste Clients", "📩 Envoi SMS", "📜 Historique SMS"])
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
    elif onglet == "📄 Liste Clients":
        liste_clients(df)
    elif onglet == "📩 Envoi SMS":
        notifier_arrivees_prochaines(df)
    elif onglet == "📜 Historique SMS":
        historique_sms()

if __name__ == "__main__":
    main()