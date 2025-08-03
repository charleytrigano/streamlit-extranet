import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import requests
import matplotlib.pyplot as plt
from io import BytesIO
import os
from dotenv import load_dotenv

# Chargement des variables d’environnement
load_dotenv()

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
        reg = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum",
            "prix_net": "sum",
            "charges": "sum",
            "%": "mean",
            "nuitees": "sum"
        }).reset_index()

        reg["prix_moyen_brut"] = (reg["prix_brut"] / reg["nuitees"]).round(2)
        reg["prix_moyen_net"] = (reg["prix_net"] / reg["nuitees"]).round(2)
        reg["mois_nom"] = reg["mois"].apply(lambda x: calendar.month_name[int(x)])

        # ➕ Totaux annuels
        totaux = data.groupby(["annee", "plateforme"]).agg({
            "prix_brut": "sum",
            "prix_net": "sum",
            "charges": "sum",
            "%": "mean",
            "nuitees": "sum"
        }).reset_index()

        totaux["prix_moyen_brut"] = (totaux["prix_brut"] / totaux["nuitees"]).round(2)
        totaux["prix_moyen_net"] = (totaux["prix_net"] / totaux["nuitees"]).round(2)

        # 💬 Affichage tableau
        st.markdown("### 📄 Détail par mois")
        st.dataframe(reg[["mois_nom", "plateforme", "prix_brut", "prix_net", "charges", "%", "nuitees", "prix_moyen_brut", "prix_moyen_net"]])

        st.markdown("### 🧾 Totaux par année")
        st.dataframe(totaux)

        # 📈 Graphique 1 : nuitées
        st.markdown("### 📊 Graphique 1 : Nuitées par mois / plateforme")
        fig1, ax1 = plt.subplots()
        pivot1 = reg.pivot(index="mois_nom", columns="plateforme", values="nuitees").fillna(0)
        pivot1.plot(kind="bar", ax=ax1)
        ax1.set_ylabel("Nuitées")
        st.pyplot(fig1)

        # 📈 Graphique 2 : revenus nets
        st.markdown("### 📊 Graphique 2 : Revenus nets par mois / plateforme")
        fig2, ax2 = plt.subplots()
        pivot2 = reg.pivot(index="mois_nom", columns="plateforme", values="prix_net").fillna(0)
        pivot2.plot(kind="bar", ax=ax2)
        ax2.set_ylabel("Revenus nets (€)")
        st.pyplot(fig2)

        # 💾 Export Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            reg.to_excel(writer, sheet_name="Par Mois", index=False)
            totaux.to_excel(writer, sheet_name="Par Annee", index=False)
            writer.save()
        output.seek(0)

        st.download_button(
            label="📥 Télécharger le rapport Excel",
            data=output,
            file_name=f"rapport_{annee}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Aucune donnée disponible pour la période sélectionnée.")

# 🚀 Lancement app
if __name__ == "__main__":
    df = charger_donnees()
    onglet = st.sidebar.radio("Navigation", ["📊 Rapport"])
    if onglet == "📊 Rapport":
        rapport_mensuel(df)