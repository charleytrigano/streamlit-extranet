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
HISTORIQUE_SMS = "sms_history.csv"
USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUM_ADMIN = "+33617722379"

# 🔤 Nettoyage
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 📤 Envoi SMS Free
def envoyer_sms(numero, message):
    params = {
        "user": USER,
        "pass": API_KEY,
        "to": numero,
        "msg": message
    }
    try:
        r = requests.get("https://smsapi.free-mobile.fr/sendmsg", params=params)
        return r.status_code == 200
    except:
        return False

# 📝 Historique CSV
def enregistrer_sms(numero, message):
    ligne = {"date": datetime.now(), "numero": numero, "message": message}
    df = pd.DataFrame([ligne])
    if os.path.exists(HISTORIQUE_SMS):
        df.to_csv(HISTORIQUE_SMS, mode='a', index=False, header=False)
    else:
        df.to_csv(HISTORIQUE_SMS, index=False)

# 🧾 Texte multi-ligne PDF
def ecrire_pdf_multiligne(pdf, texte, largeur_max=270):
    mots = texte.split()
    ligne = ""
    for mot in mots:
        if len(ligne + " " + mot) < largeur_max:
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

# 📥 Charger données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

# ➕ Ajouter
def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajout"):
        nom = st.text_input("Nom")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        tel = st.text_input("Téléphone")
        arrivee = st.date_input("Date arrivée")
        depart = st.date_input("Date départ", min_value=arrivee + timedelta(days=1))
        brut = st.number_input("Prix brut", min_value=0.0)
        net = st.number_input("Prix net", min_value=0.0, max_value=brut)
        submit = st.form_submit_button("Enregistrer")
        if submit:
            ligne = {
                "nom_client": nom,
                "plateforme": plateforme,
                "telephone": tel,
                "date_arrivee": arrivee,
                "date_depart": depart,
                "prix_brut": round(brut, 2),
                "prix_net": round(net, 2),
                "charges": round(brut - net, 2),
                "%": round((brut - net) / brut * 100 if brut else 0, 2),
                "nuitees": (depart - arrivee).days,
                "annee": arrivee.year,
                "mois": arrivee.month
            }
            df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation enregistrée")
    return df

# ✏️ Modifier
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
            df.at[i, "%"] = round((brut - net) / brut * 100 if brut else 0, 2)
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
            jour_date = date(annee, mois_index, jour) if jour else None
            contenu = f"{jour}\n" + "\n".join(planning.get(jour_date, [])) if jour_date else ""
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
        data = data[data["mois"] == mois]
    if not data.empty:
        data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit"]
        st.dataframe(data[colonnes])

        # Export Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            data[colonnes].to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger la liste", data=buffer, file_name=f"liste_clients_{annee}_{mois}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune donnée pour cette période.")

# 📜 Historique SMS
def afficher_historique_sms():
    st.subheader("📬 Historique SMS")
    if os.path.exists(HISTORIQUE_SMS):
        df = pd.read_csv(HISTORIQUE_SMS)
        st.dataframe(df)
    else:
        st.info("Aucun SMS envoyé pour le moment.")

# ▶️ Main
def main():
    st.sidebar.title("Menu")
    onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📋 Liste Clients", "📬 Historique SMS"])

    df = charger_donnees()

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
        st.subheader("📊 Rapport mensuel")
        st.info("Fonction désactivée — uniquement Excel disponible pour fiabilité.")

    elif onglet == "📋 Liste Clients":
        liste_clients(df)

    elif onglet == "📬 Historique SMS":
        afficher_historique_sms()

if __name__ == "__main__":
    main()