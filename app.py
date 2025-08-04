import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata

FICHIER = "reservations.xlsx"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def ecrire_pdf_multiligne(pdf, texte, largeur_max=160):
    try:
        lignes = [texte[i:i+largeur_max] for i in range(0, len(texte), largeur_max)]
        for ligne in lignes:
            pdf.multi_cell(0, 8, ligne)
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).round(2)
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    df["annee"] = df["date_arrivee"].dt.year
    df["mois"] = df["date_arrivee"].dt.month
    return df

def exporter_pdf(data, annee):
    pdf = FPDF(orientation="L", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, txt=f"Rapport Reservations - {annee}", ln=True, align="C")
    pdf.ln(5)
    for _, row in data.iterrows():
        row = row.fillna("")
        texte = (
            f"{row['annee']} {row['mois']} | Plateforme: {row['plateforme']} | Nuitées: {row['nuitees']} | "
            f"Brut: {row['prix_brut']:.2f}€ | Net: {row['prix_net']:.2f}€ | Charges: {row['charges']:.2f}€ | "
            f"Moy. brut/nuit: {row['prix_moyen_brut']:.2f}€ | Moy. net/nuit: {row['prix_moyen_net']:.2f}€"
        )
        ecrire_pdf_multiligne(pdf, nettoyer_texte(texte), largeur_max=160)
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df[df["annee"] == annee]["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        reg = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum", "prix_net": "sum", "charges": "sum", "%": "mean", "nuitees": "sum"
        }).reset_index()
        reg["prix_moyen_brut"] = (reg["prix_brut"] / reg["nuitees"]).round(2)
        reg["prix_moyen_net"] = (reg["prix_net"] / reg["nuitees"]).round(2)
        st.dataframe(reg)

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

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        pdf_buffer = exporter_pdf(reg, annee)
        st.download_button("📄 Télécharger PDF", data=pdf_buffer, file_name=f"rapport_{annee}.pdf", mime="application/pdf")
    else:
        st.info("Aucune donnée pour cette période.")

def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df[df["annee"] == annee]["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if data.empty:
        st.info("Aucune donnée pour cette période.")
    else:
        cols = ["nom_client", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net"]
        st.dataframe(data[cols].sort_values(by=["date_arrivee"]))

def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", [
        "📋 Réservations", "📋 Liste clients", "📊 Rapport"
    ])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df)
    elif onglet == "📋 Liste clients":
        liste_clients(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)

if __name__ == "__main__":
    main()