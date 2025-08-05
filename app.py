import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata

FICHIER = "reservations.xlsx"

# 🔤 Nettoyer accents & caractères spéciaux
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 🧾 Multi-ligne PDF sécurisé
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    mots = texte.split()
    ligne = ""
    for mot in mots:
        if pdf.get_string_width(ligne + " " + mot) < largeur_max:
            ligne += " " + mot
        else:
            try:
                pdf.multi_cell(0, 8, ligne.strip())
            except:
                pdf.multi_cell(0, 8, "<ligne non imprimable>")
            ligne = mot
    if ligne:
        try:
            pdf.multi_cell(0, 8, ligne.strip())
        except:
            pdf.multi_cell(0, 8, "<ligne non imprimable>")

# 📥 Charger données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
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
        prix_brut = st.number_input("Prix brut", min_value=0.0, step=0.01, format="%.2f")
        prix_net = st.number_input("Prix net", min_value=0.0, max_value=prix_brut, step=0.01, format="%.2f")
        submit = st.form_submit_button("Enregistrer")
        if submit:
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

# ✏️ Modifier / Supprimer
def modifier_reservation(df):
    st.subheader("✏️ Modifier / Supprimer")
    df["identifiant"] = df["nom_client"] + " | " + pd.to_datetime(df["date_arrivee"]).dt.strftime('%Y-%m-%d')
    selection = st.selectbox("Choisissez une réservation", df["identifiant"])
    i = df[df["identifiant"] == selection].index[0]
    with st.form("modif"):
        nom = st.text_input("Nom", df.at[i, "nom_client"])
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(df.at[i, "plateforme"]))
        tel = st.text_input("Téléphone", df.at[i, "telephone"])
        arrivee = st.date_input("Arrivée", df.at[i, "date_arrivee"])
        depart = st.date_input("Départ", df.at[i, "date_depart"])
        brut = st.number_input("Prix brut", value=float(df.at[i, "prix_brut"]), step=0.01, format="%.2f")
        net = st.number_input("Prix net", value=float(df.at[i, "prix_net"]), step=0.01, format="%.2f")
        submit = st.form_submit_button("Modifier")
        delete = st.form_submit_button("Supprimer")
        if submit:
            df.at[i, "nom_client"] = nom
            df.at[i, "plateforme"] = plateforme
            df.at[i, "telephone"] = tel
            df.at[i, "date_arrivee"] = arrivee
            df.at[i, "date_depart"] = depart
            df.at[i, "prix_brut"] = round(brut, 2)
            df.at[i, "prix_net"] = round(net, 2)
            df.at[i, "charges"] = round(brut - net, 2)
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

# 🧾 Liste des clients
def liste_clients(df):
    st.subheader("📄 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].dropna().unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]

    if not data.empty:
        data_affichee = data[[
            "nom_client", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "plateforme"
        ]].copy()

        data_affichee["prix_brut"] = data_affichee["prix_brut"].round(2)
        data_affichee["prix_net"] = data_affichee["prix_net"].round(2)
        data_affichee["charges"] = data_affichee["charges"].round(2)
        data_affichee["%"] = data_affichee["%"].round(2)
        data_affichee["prix_moyen_brut"] = (data_affichee["prix_brut"] / data_affichee["nuitees"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
        data_affichee["prix_moyen_net"] = (data_affichee["prix_net"] / data_affichee["nuitees"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)

        total = pd.DataFrame(data_affichee[[
            "nuitees", "prix_brut", "prix_net", "charges"
        ]].sum()).T
        total["nom_client"] = "TOTAL"
        total["date_arrivee"] = ""
        total["date_depart"] = ""
        total["%"] = (total["charges"] / total["prix_brut"] * 100).round(2)
        total["plateforme"] = ""
        total["prix_moyen_brut"] = (total["prix_brut"] / total["nuitees"]).round(2)
        total["prix_moyen_net"] = (total["prix_net"] / total["nuitees"]).round(2)

        data_affichee = pd.concat([data_affichee, total], ignore_index=True)
        st.dataframe(data_affichee)

    else:
        st.info("Aucune donnée pour cette période.")

# ▶️ Lancement
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📄 Liste des clients", "📊 Rapport"])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📄 Liste des clients":
        liste_clients(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)

if __name__ == "__main__":
    main()