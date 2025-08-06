

import streamlit as st
from data_loader import charger_donnees, telecharger_fichier_excel, uploader_excel
from views import afficher_reservations, ajouter_reservation, modifier_reservation, afficher_calendrier, afficher_rapport, liste_clients
from sms import notifier_arrivees_prochaines, historique_sms

def main():
    st.sidebar.markdown("## 📤 Importer un fichier Excel")
    uploader_excel()

    df = charger_donnees()
    if df.empty:
        st.warning("Aucune donnée disponible. Veuillez importer un fichier Excel.")
        return

    notifier_arrivees_prochaines(df)

    onglet = st.sidebar.radio("Menu", [
        "📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer",
        "📅 Calendrier", "📊 Rapport", "👥 Liste clients", "✉️ Historique SMS"
    ])

    if onglet == "📋 Réservations":
        afficher_reservations(df)
        telecharger_fichier_excel(df)

    elif onglet == "➕ Ajouter":
        ajouter_reservation(df)

    elif onglet == "✏️ Modifier / Supprimer":
        modifier_reservation(df)

    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)

    elif onglet == "📊 Rapport":
        afficher_rapport(df)

    elif onglet == "👥 Liste clients":
        liste_clients(df)

    elif onglet == "✉️ Historique SMS":
        historique_sms()

if __name__ == "__main__":
    main()

import pandas as pd
import streamlit as st
from io import BytesIO
import base64
import os

FICHIER = "reservations.xlsx"

def charger_donnees():
    if not os.path.exists(FICHIER):
        return pd.DataFrame()
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

def telecharger_fichier_excel(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{FICHIER}">📥 Télécharger reservations.xlsx</a>'
    st.markdown(href, unsafe_allow_html=True)

def uploader_excel():
    fichier = st.file_uploader("Importer un fichier Excel", type="xlsx")
    if fichier:
        with open(FICHIER, "wb") as f:
            f.write(fichier.read())
        st.success("✅ Fichier importé avec succès. Rechargez l'app si nécessaire.")

import pandas as pd
import streamlit as st
from io import BytesIO
import base64
import os

FICHIER = "reservations.xlsx"

def charger_donnees():
    if not os.path.exists(FICHIER):
        return pd.DataFrame()
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

def telecharger_fichier_excel(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{FICHIER}">📥 Télécharger reservations.xlsx</a>'
    st.markdown(href, unsafe_allow_html=True)

def uploader_excel():
    fichier = st.file_uploader("Importer un fichier Excel", type="xlsx")
    if fichier:
        with open(FICHIER, "wb") as f:
            f.write(fichier.read())
        st.success("✅ Fichier importé avec succès. Rechargez l'app si nécessaire.")

import streamlit as st import pandas as pd import calendar from datetime import date, timedelta, datetime import matplotlib.pyplot as plt from fpdf import FPDF from io import BytesIO import unicodedata import requests import os import base64

FICHIER = "reservations.xlsx" SMS_HISTO = "historique_sms.csv"

FREE_USER = "12026027" FREE_API_KEY = "MF7Qjs3C8KxKHz" NUM_TELEPHONE_PERSO = "+33617722379"

🔤 Nettoyer accents & caractères spéciaux

def nettoyer_texte(s): if isinstance(s, str): return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii') return str(s)

📥 Chargement fichier Excel

def charger_donnees(): if not os.path.exists(FICHIER): return pd.DataFrame() df = pd.read_excel(FICHIER) df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date df = df[df["date_arrivee"].notna() & df["date_depart"].notna()] df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2) df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2) df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2) df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2) df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"]).dt.date).dt.days df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month return df

📥 Téléchargement du fichier Excel

def telecharger_fichier_excel(df): buffer = BytesIO() df.to_excel(buffer, index=False) buffer.seek(0) b64 = base64.b64encode(buffer.read()).decode() href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="reservations.xlsx">📥 Télécharger reservations.xlsx</a>' st.markdown(href, unsafe_allow_html=True)

📤 Recharger un fichier Excel

def uploader_excel(): fichier = st.file_uploader("Recharger un fichier reservations.xlsx", type="xlsx") if fichier: with open(FICHIER, "wb") as f: f.write(fichier.read()) st.success("✅ Fichier importé avec succès. Veuillez recharger l'application.")

➕ Ajouter réservation

def ajouter_reservation(df): st.subheader("➕ Nouvelle Réservation") with st.form("ajout"): nom = st.text_input("Nom") plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"]) tel = st.text_input("Téléphone") arrivee = st.date_input("Date arrivée") depart = st.date_input("Date départ", min_value=arrivee + timedelta(days=1)) col1, col2 = st.columns(2) with col1: prix_brut = st.number_input("Prix brut", min_value=0.0, key="prix_brut_ajout") with col2: prix_net = st.number_input("Prix net", min_value=0.0, key="prix_net_ajout")

submit = st.form_submit_button("Enregistrer")
    if submit:
        if prix_net > prix_brut:
            st.error("Le prix net ne peut pas être supérieur au prix brut.")
        else:
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

✏️ Modifier réservation (déjà présent, inchangé)

📅 Calendrier

📊 Rapport

👥 Liste clients

✉️ Historique SMS

Notifier arrivées prochaines (déjà présentes, inchangées)

▶️ Application principale

def main(): st.sidebar.markdown("## 📤 Importer des données") uploader_excel()

df = charger_donnees()
if df.empty:
    st.warning("Aucune donnée disponible. Veuillez importer un fichier.")
    return

notifier_arrivees_prochaines(df)

onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "👥 Liste clients", "✉️ Historique SMS"])

if onglet == "📋 Réservations":
    st.title("📋 Réservations")
    st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    telecharger_fichier_excel(df)
elif onglet == "➕ Ajouter":
    df = ajouter_reservation(df)
elif onglet == "✏️ Modifier / Supprimer":
    df = modifier_reservation(df)
elif onglet == "📅 Calendrier":
    afficher_calendrier(df)
elif onglet == "📊 Rapport":
    afficher_rapport(df)
elif onglet == "👥 Liste clients":
    liste_clients(df)
elif onglet == "✉️ Historique SMS":
    historique_sms()

if name == "main": main()

