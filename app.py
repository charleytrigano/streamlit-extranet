import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import os
from send_sms import envoyer_sms

FICHIER = "reservations.xlsx"
HISTORIQUE_SMS = "historique_sms.csv"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        mots = texte.split()
        ligne = ""
        for mot in mots:
            if pdf.get_string_width(ligne + " " + mot) > largeur_max:
                pdf.multi_cell(0, 8, ligne)
                ligne = mot
            else:
                ligne += " " + mot if ligne else mot
        if ligne:
            pdf.multi_cell(0, 8, ligne)
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

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

def liste_clients(df):
    st.subheader("📇 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()), key="liste_annee")
    mois = st.selectbox("Mois", sorted(df[df["annee"] == annee]["mois"].unique()), key="liste_mois")
    data = df[(df["annee"] == annee) & (df["mois"] == mois)].copy()
    if data.empty:
        st.info("Aucune donnée pour cette période.")
        return
    data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).round(2)
    data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).round(2)
    colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit", "telephone"]
    st.dataframe(data[colonnes])

    st.markdown("### 📤 Envoi manuel des SMS")
    for _, row in data.iterrows():
        with st.expander(f"{row['nom_client']} ({row['date_arrivee']} - {row['date_depart']})"):
            message = (
                f"VILLA TOBIAS - {row['plateforme']}\n"
                f"Bonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}."
                " Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. Nous vous rappelons qu’un parking est à votre disposition sur place. À demain"
            )
            st.text_area("SMS à envoyer :", message, height=100, key=f"sms_{row['nom_client']}")
            if st.button("📩 Envoyer SMS", key=f"btn_{row['nom_client']}"):
                try:
                    envoyer_sms(row["telephone"], message)
                    log = {
                        "date_envoi": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "nom_client": row["nom_client"],
                        "telephone": row["telephone"],
                        "message": message
                    }
                    if os.path.exists(HISTORIQUE_SMS):
                        pd.concat([pd.read_csv(HISTORIQUE_SMS), pd.DataFrame([log])], ignore_index=True).to_csv(HISTORIQUE_SMS, index=False)
                    else:
                        pd.DataFrame([log]).to_csv(HISTORIQUE_SMS, index=False)
                    st.success("✅ SMS envoyé")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    if os.path.exists(HISTORIQUE_SMS):
        st.markdown("### 📜 Historique des SMS")
        histo = pd.read_csv(HISTORIQUE_SMS)
        st.dataframe(histo)

# ➕ Ajouter, ✏️ Modifier/Supprimer et 📅 Calendrier ici comme déjà intégré

# 📊 Rapport mensuel (à inclure ici comme déjà corrigé, sans PDF)

# ▶️ Lancement
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📇 Liste Clients"])
    if onglet == "📇 Liste Clients":
        liste_clients(df)
    elif onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df)
    # autres onglets à coller ici depuis ton script précédent

if __name__ == "__main__":
    main()