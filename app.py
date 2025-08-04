import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

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

# 📄 Générer PDF
def exporter_pdf(data, annee):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Rapport de l'année {annee}", ln=True)

    pdf.set_font("Arial", "", 10)
    for _, row in data.iterrows():
        ligne = (
            f"{row['nom_client']} | {row['plateforme']} | "
            f"{row['date_arrivee'].strftime('%Y-%m-%d')} -> {row['date_depart'].strftime('%Y-%m-%d')} | "
            f"{row['nuitees']} nuits | Brut: {row['prix_brut']} € | Net: {row['prix_net']} €"
        )
        pdf.multi_cell(0, 8, ligne)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# 📊 Rapport
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
        reg["mois"] = reg["mois"].apply(lambda x: calendar.month_name[int(x)])

        st.dataframe(reg.style.format({
            "prix_brut": "€{:.2f}", "prix_net": "€{:.2f}",
            "charges": "€{:.2f}", "%": "{:.2f}%",
            "prix_moyen_brut": "€{:.2f}", "prix_moyen_net": "€{:.2f}",
            "nuitees": "{:.0f}"
        }))

        # Graphiques
        st.markdown("### 📈 Nuitées par mois")
        pivot_nuits = data.pivot_table(index="mois", columns="plateforme", values="nuitees", aggfunc="sum").fillna(0)
        pivot_nuits.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf())
        plt.clf()

        st.markdown("### 📈 Total Net par mois")
        pivot_net = data.pivot_table(index="mois", columns="plateforme", values="prix_net", aggfunc="sum").fillna(0)
        pivot_net.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf())
        plt.clf()

        # Export Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            reg.to_excel(writer, index=False)
        excel_buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=excel_buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Export PDF
        pdf_buffer = exporter_pdf(data, annee)
        st.download_button("📄 Télécharger PDF", data=pdf_buffer, file_name=f"rapport_{annee}.pdf", mime="application/pdf")
    else:
        st.info("Aucune donnée disponible")

# Autres fonctions (réservations, ajout, modification, calendrier) ici ⬇️

# 🚀 Main
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "📊 Rapport"])

    if onglet == "📋 Réservations":
        st.title("📋 Tableau des réservations")
        st.dataframe(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)

if __name__ == "__main__":
    main()