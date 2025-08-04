import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
import ssl
import os
from dotenv import load_dotenv

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

# 📊 Rapport PDF
def generer_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "📄 Rapport Réservations", ln=True, align="C")

    grouped = data.groupby(["annee", "mois", "plateforme"])
    for (annee, mois, plateforme), group in grouped:
        pdf.set_font("Arial", "B", 12)
        titre = f"{calendar.month_name[mois]} {annee} - {plateforme}"
        pdf.cell(200, 10, titre, ln=True)

        # En-têtes
        pdf.set_font("Arial", "B", 9)
        headers = ["Client", "Arrivée", "Départ", "Nuits", "Brut", "Net"]
        for h in headers:
            pdf.cell(32, 7, h, border=1)
        pdf.ln()

        pdf.set_font("Arial", "", 9)
        for _, row in group.iterrows():
            pdf.cell(32, 6, str(row["nom_client"]), border=1)
            pdf.cell(32, 6, row["date_arrivee"].strftime("%d/%m"), border=1)
            pdf.cell(32, 6, row["date_depart"].strftime("%d/%m"), border=1)
            pdf.cell(32, 6, str(row["nuitees"]), border=1)
            pdf.cell(32, 6, f"{row['prix_brut']:.2f}", border=1)
            pdf.cell(32, 6, f"{row['prix_net']:.2f}", border=1)
            pdf.ln()

        # Totaux
        total_brut = group["prix_brut"].sum()
        total_net = group["prix_net"].sum()
        pdf.set_font("Arial", "B", 9)
        pdf.cell(128, 7, "TOTAL", border=1)
        pdf.cell(32, 7, f"{total_brut:.2f}", border=1)
        pdf.cell(32, 7, f"{total_net:.2f}", border=1)
        pdf.ln(10)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

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
        reg["mois"] = reg["mois"].apply(lambda x: calendar.month_name[int(x)])

        st.dataframe(reg.style.format({
            "prix_brut": "€{:.2f}", "prix_net": "€{:.2f}",
            "charges": "€{:.2f}", "%": "{:.2f}%",
            "prix_moyen_brut": "€{:.2f}", "prix_moyen_net": "€{:.2f}",
            "nuitees": "{:.0f}"
        }))

        # 📈 Graphiques
        st.markdown("### 📈 Graphique : Nuitées par mois par plateforme")
        pivot_nuits = data.pivot_table(index="mois", columns="plateforme", values="nuitees", aggfunc="sum").fillna(0)
        pivot_nuits.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf())
        plt.clf()

        st.markdown("### 📈 Graphique : Total Net par mois par plateforme")
        pivot_net = data.pivot_table(index="mois", columns="plateforme", values="prix_net", aggfunc="sum").fillna(0)
        pivot_net.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf())
        plt.clf()

        # 📥 Télécharger Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # 📄 PDF
        pdf_buffer = generer_pdf(data)
        st.download_button("📄 Télécharger PDF", data=pdf_buffer, file_name=f"rapport_{annee}.pdf", mime="application/pdf")

        # 📧 Envoi email
        st.markdown("### ✉️ Envoyer le rapport PDF par e-mail")
        if st.button("Envoyer"):
            load_dotenv()
            sender = os.getenv("EMAIL_USER")
            password = os.getenv("EMAIL_PASS")
            to_list = os.getenv("DESTINATAIRES", "").split(",")

            msg = EmailMessage()
            msg["Subject"] = f"📄 Rapport Réservations {annee}"
            msg["From"] = sender
            msg["To"] = ", ".join(to_list)
            msg.set_content("Veuillez trouver ci-joint le rapport PDF des réservations.")

            msg.add_attachment(pdf_buffer.getvalue(), maintype='application', subtype='pdf', filename=f"rapport_{annee}.pdf")

            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender, password)
                    server.send_message(msg)
                st.success("📧 Email envoyé avec succès.")
            except Exception as e:
                st.error(f"Erreur d'envoi : {e}")
    else:
        st.info("Aucune donnée pour cette période.")

# 🚀 Lancement
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "➕ Ajouter", "📊 Rapport"])
    if onglet == "📋 Réservations":
        st.title("📋 Tableau des réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)

if __name__ == "__main__":
    main()