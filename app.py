import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar
import os
import requests

# ---------- CONFIGURATION ----------
FICHIER_EXCEL = "reservations.xlsx"

FREE_API_ENDPOINT = "https://smsapi.free-mobile.fr/sendmsg"
FREE_API_CREDENTIALS = [
    {"user": "12026027", "key": "1Pat6vSRCLiSXl", "telephone": "+33611772793"},
    {"user": "12026027", "key": "MF7Qjs3C8KxKHz", "telephone": "+33617722379"}
]

# ---------- FONCTIONS DE BASE ----------

def charger_donnees():
    df = pd.read_excel(FICHIER_RESERVATIONS)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    df["charges"] = df["prix_brut"] - df["prix_net"]
    df["%"] = (df["charges"] / df["prix_brut"] * 100).round(2)
    return df

def sauvegarder_donnees(df):
    df.to_excel(FICHIER_RESERVATIONS, index=False)

# --- Interface principale
def interface_modifier_supprimer(df):
    st.subheader("Modifier ou Supprimer une Réservation")

    # Conversion sécurisée pour affichage
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_arrivee_str"] = df["date_arrivee"].dt.strftime('%Y-%m-%d')
    df["date_arrivee_str"] = df["date_arrivee_str"].fillna("Date invalide")

    df["label"] = df["nom_client"] + " | " + df["date_arrivee_str"]
    selected_label = st.selectbox("Choisissez un client", df["label"])

    index = df[df["label"] == selected_label].index[0]
    row = df.loc[index]

    nom_client = st.text_input("Nom client", row["nom_client"])
    plateforme = st.text_input("Plateforme", row["plateforme"])
    telephone = st.text_input("Téléphone", row["telephone"])
    date_arrivee = st.date_input("Date arrivée", row["date_arrivee"])
    date_depart = st.date_input("Date départ", row["date_depart"])
    prix_brut = st.number_input("Prix brut", value=float(row["prix_brut"]))
    prix_net = st.number_input("Prix net", value=float(row["prix_net"]))

    if st.button("✅ Enregistrer les modifications"):
        df.at[index, "nom_client"] = nom_client
        df.at[index, "plateforme"] = plateforme
        df.at[index, "telephone"] = telephone
        df.at[index, "date_arrivee"] = date_arrivee
        df.at[index, "date_depart"] = date_depart
        df.at[index, "prix_brut"] = prix_brut
        df.at[index, "prix_net"] = prix_net
        df.at[index, "charges"] = prix_brut - prix_net
        df.at[index, "%"] = round((prix_brut - prix_net) / prix_brut * 100, 2)
        df.at[index, "nuitees"] = (date_depart - date_arrivee).days
        sauvegarder_donnees(df)
        st.success("✅ Réservation mise à jour.")

    if st.button("🗑️ Supprimer cette réservation"):
        df = df.drop(index)
        sauvegarder_donnees(df)
        st.success("🗑️ Réservation supprimée.")

# --- Affichage rapport mensuel
def rapport_mensuel(df):
    st.subheader("📊 Rapport Mensuel")

    df["annee"] = df["date_arrivee"].dt.year
    df["mois"] = df["date_arrivee"].dt.month

    annee = st.selectbox("Filtrer par année", sorted(df["annee"].unique()))
    mois = st.selectbox("Filtrer par mois", sorted(df[df["annee"] == annee]["mois"].unique()))

    df_filtre = df[(df["annee"] == annee) & (df["mois"] == mois)]

    if df_filtre.empty:
        st.warning("Aucune donnée pour ce mois.")
        return

    total_ligne = df_filtre[["prix_brut", "prix_net", "charges", "%", "nuitees"]].sum(numeric_only=True)
    total_ligne["%"] = round(total_ligne["%"] / len(df_filtre), 2)

    st.dataframe(pd.concat([df_filtre, pd.DataFrame([total_ligne], index=["Total"])]))

# --- Page principale
def main():
    st.set_page_config(layout="wide")
    st.title("📅 Gestion des Réservations")

    onglet = st.sidebar.radio("Navigation", ["📁 Tableau Réservations", "✏️ Modifier/Supprimer", "📊 Rapport Mensuel"])

    df = charger_donnees()

    if onglet == "📁 Tableau Réservations":
        st.dataframe(df)

    elif onglet == "✏️ Modifier/Supprimer":
        interface_modifier_supprimer(df)

    elif onglet == "📊 Rapport Mensuel":
        rapport_mensuel(df)

if __name__ == "__main__":
    main()
