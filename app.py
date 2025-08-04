import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
import os

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

# 🧹 Nettoyer texte PDF
def nettoyer_texte(texte):
    return ''.join(c if ord(c) < 128 else '?' for c in str(texte))

# 🧾 Export PDF
def exporter_pdf(data, annee):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Rapport des réservations - Année {annee}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)

    for _, row in data.iterrows():
        ligne = f"{row['mois']}, {row['plateforme']}: {row['nuitees']} nuitées, Net: {row['prix_net']}€"
        texte_nettoye = nettoyer_texte(ligne)
        for chunk in [texte_nettoye[i:i+100] for i in range(0, len(texte_nettoye), 100)]:
            pdf.multi_cell(0, 8, chunk)

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
        st.dataframe(reg)

        # Graphiques
        pivot1 = data.pivot_table(index="mois", columns="plateforme", values="nuitees", aggfunc="sum").fillna(0)
        st.markdown("### 📈 Nuitées par mois")
        pivot1.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf()); plt.clf()

        pivot2 = data.pivot_table(index="mois", columns="plateforme", values="prix_net", aggfunc="sum").fillna(0)
        st.markdown("### 📈 Total Net par mois")
        pivot2.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf()); plt.clf()

        # Export Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        st.download_button("📥 Export Excel", buffer.getvalue(), file_name=f"rapport_{annee}.xlsx")

        # Export PDF
        pdf_buffer = exporter_pdf(data, annee)
        st.download_button("📄 Export PDF", pdf_buffer, file_name=f"rapport_{annee}.pdf")

    else:
        st.info("Aucune donnée disponible")

# 🚀 Lancement
def main():
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

if __name__ == "__main__":
    main()