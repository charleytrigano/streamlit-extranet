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
from send_sms import send_sms  # fichier séparé pour l'envoi
import csv

FICHIER = "reservations.xlsx"
SMS_LOG = "historique_sms.csv"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        mots = texte.split()
        ligne = ""
        for mot in mots:
            if len(ligne + " " + mot) <= largeur_max:
                ligne += " " + mot
            else:
                pdf.multi_cell(0, 8, ligne.strip())
                ligne = mot
        if ligne:
            pdf.multi_cell(0, 8, ligne.strip())
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

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

def exporter_pdf(data, annee):
    pdf = FPDF(orientation="L", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, txt=f"Rapport Reservations - {annee}", ln=True, align="C")
    pdf.ln(5)
    for _, row in data.iterrows():
        texte = (
            f"{row['annee']} {row['mois']} | Plateforme: {row['plateforme']} | Nuitées: {int(row['nuitees'])} | "
            f"Brut: {row['prix_brut']}€ | Net: {row['prix_net']}€ | Charges: {row['charges']}€ | "
            f"%: {row['%']} | Moy. brut/nuit: {row['prix_moyen_brut']}€ | Moy. net/nuit: {row['prix_moyen_net']}€"
        )
        ecrire_pdf_multiligne_safe(pdf, nettoyer_texte(texte))
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        reg = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum", "prix_net": "sum", "charges": "sum", "%": "mean", "nuitees": "sum"
        }).reset_index()
        reg["prix_moyen_brut"] = (reg["prix_brut"] / reg["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        reg["prix_moyen_net"] = (reg["prix_net"] / reg["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
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

        # Export
        with BytesIO() as buffer:
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
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]

    if not data.empty:
        data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit"]
        st.dataframe(data[colonnes])

        total = pd.DataFrame(data[colonnes].sum(numeric_only=True)).T
        total["nom_client"] = "TOTAL"
        st.dataframe(pd.concat([data[colonnes], total], ignore_index=True))

        # Export Excel
        with BytesIO() as buffer:
            data[colonnes].to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button("📥 Télécharger liste clients", data=buffer, file_name="liste_clients.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def afficher_historique_sms():
    st.subheader("📨 Historique des SMS envoyés")
    if os.path.exists(SMS_LOG):
        df_sms = pd.read_csv(SMS_LOG)
        st.dataframe(df_sms)
    else:
        st.info("Aucun SMS encore envoyé.")

def envoyer_sms_clients(df):
    st.subheader("📤 SMS à envoyer manuellement")
    demain = date.today() + timedelta(days=1)
    df_sms = df[df["date_arrivee"] == demain]
    if df_sms.empty:
        st.info("Aucun client prévu demain.")
        return
    for _, row in df_sms.iterrows():
        message = f"""VILLA TOBIAS - {row['plateforme']}
Bonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}. Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. Nous vous rappelons qu'un parking est à votre disposition sur place. À demain"""
        st.write(message)
        if st.button(f"📩 Envoyer à {row['nom_client']}"):
            send_sms(row['telephone'], message)
            with open(SMS_LOG, "a", newline="") as f:
                writer = csv.writer(f)
                if f.tell() == 0:
                    writer.writerow(["date", "client", "telephone", "message"])
                writer.writerow([date.today(), row["nom_client"], row["telephone"], message])
            st.success(f"SMS envoyé à {row['nom_client']}")

def main():
    st.set_page_config(page_title="Extranet VILLA TOBIAS", layout="wide")
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", [
        "📋 Réservations",
        "➕ Ajouter",
        "✏️ Modifier / Supprimer",
        "📅 Calendrier",
        "📊 Rapport",
        "📋 Liste clients",
        "📨 Historique SMS",
        "📤 SMS à envoyer"
    ])

    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        st.info("Formulaire à venir...")
    elif onglet == "✏️ Modifier / Supprimer":
        st.info("Fonctionnalité à venir...")
    elif onglet == "📅 Calendrier":
        st.info("Affichage calendrier à venir...")
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)
    elif onglet == "📋 Liste clients":
        liste_clients(df)
    elif onglet == "📨 Historique SMS":
        afficher_historique_sms()
    elif onglet == "📤 SMS à envoyer":
        envoyer_sms_clients(df)

if __name__ == "__main__":
    main()