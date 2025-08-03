import streamlit as st
import pandas as pd
import calendar
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
import requests
from io import BytesIO

FICHIER = "reservations.xlsx"

# 📦 Chargement des données
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
    df["plateforme"] = df["plateforme"].fillna("Autre")
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
            charges = prix_brut - prix_net
            pourcent = (charges / prix_brut * 100) if prix_brut else 0
            nuitees = (depart - arrivee).days
            ligne = {
                "nom_client": nom, "plateforme": plateforme, "telephone": tel,
                "date_arrivee": arrivee, "date_depart": depart,
                "prix_brut": prix_brut, "prix_net": prix_net,
                "charges": charges, "%": round(pourcent, 2),
                "nuitees": nuitees, "annee": arrivee.year, "mois": arrivee.month
            }
            df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation enregistrée")
    return df

# ✏️ Modifier / supprimer réservation
def modifier_reservation(df):
    st.subheader("✏️ Modifier ou Supprimer une Réservation")
    df["identifiant"] = df["nom_client"] + " | " + df["date_arrivee"].dt.strftime('%Y-%m-%d')
    selection = st.selectbox("Choisissez une réservation", df["identifiant"])
    i = df[df["identifiant"] == selection].index[0]
    with st.form("modif"):
        nom = st.text_input("Nom", df.at[i, "nom_client"])
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(df.at[i, "plateforme"]))
        tel = st.text_input("Téléphone", df.at[i, "telephone"])
        arrivee = st.date_input("Arrivée", df.at[i, "date_arrivee"].date())
        depart = st.date_input("Départ", df.at[i, "date_depart"].date())
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
            df.at[i, "charges"] = brut - net
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

# 📊 Rapport mensuel
def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    mois = st.selectbox("Filtre mois", ["Tous"] + sorted(df["mois"].unique()))
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]

    if not data.empty:
        regroup = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum",
            "prix_net": "sum",
            "charges": "sum",
            "%": "mean",
            "nuitees": "sum"
        }).reset_index()

        regroup["prix_moyen_brut"] = (regroup["prix_brut"] / regroup["nuitees"]).round(2)
        regroup["prix_moyen_net"] = (regroup["prix_net"] / regroup["nuitees"]).round(2)
        regroup["mois_nom"] = regroup["mois"].apply(lambda x: calendar.month_name[int(x)])
        regroup = regroup[["annee", "mois_nom", "plateforme", "prix_brut", "prix_net", "charges", "%", "nuitees", "prix_moyen_brut", "prix_moyen_net"]]

        st.dataframe(regroup.style.format({
            "prix_brut": "€{:.2f}", "prix_net": "€{:.2f}",
            "charges": "€{:.2f}", "%": "{:.2f}%", "prix_moyen_brut": "€{:.2f}", "prix_moyen_net": "€{:.2f}"
        }))

        # Graphique 1 : Nuitéés
        fig1, ax1 = plt.subplots()
        for plateforme in regroup["plateforme"].unique():
            subset = regroup[regroup["plateforme"] == plateforme]
            ax1.plot(subset["mois_nom"], subset["nuitees"], label=plateforme, marker="o")
        ax1.set_title("Nuitées par mois et plateforme")
        ax1.set_ylabel("Nuitées")
        ax1.set_xlabel("Mois")
        ax1.legend()
        st.pyplot(fig1)

        # Graphique 2 : Net
        fig2, ax2 = plt.subplots()
        for plateforme in regroup["plateforme"].unique():
            subset = regroup[regroup["plateforme"] == plateforme]
            ax2.plot(subset["mois_nom"], subset["prix_net"], label=plateforme, marker="o")
        ax2.set_title("Total net par mois et plateforme")
        ax2.set_ylabel("Prix net (€)")
        ax2.set_xlabel("Mois")
        ax2.legend()
        st.pyplot(fig2)

        # Bouton export
        buffer = BytesIO()
        regroup.to_excel(buffer, index=False)
        st.download_button("📥 Télécharger le rapport Excel", buffer.getvalue(), file_name="rapport.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune donnée disponible.")

# 🚀 Lancement de l'app
if __name__ == "__main__":
    df = charger_donnees()
    onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📊 Rapport"])

    if onglet == "📋 Réservations":
        st.title("📋 Tableau des réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)