# 🔧 IMPORTS
import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import os
from send_sms import envoyer_sms  # <-- Script externe
import csv

# 📁 FICHIERS
FICHIER = "reservations.xlsx"
HISTORIQUE_SMS = "sms_history.csv"

# 🔤 NETTOYAGE TEXTE
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 📤 SMS AUTO 24H AVANT
def notifier_arrivees_prochaines(df):
    if not os.path.exists(HISTORIQUE_SMS):
        with open(HISTORIQUE_SMS, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["nom_client", "telephone", "date_arrivee", "date_envoi"])

    demain = date.today() + timedelta(days=1)
    df_notif = df[df["date_arrivee"] == pd.to_datetime(demain)]

    for _, row in df_notif.iterrows():
        if row["telephone"] and row["nom_client"]:
            msg = (
                f"VILLA TOBIAS - {row['plateforme']}\n"
                f"Bonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee'].date()} au {row['date_depart'].date()}. "
                f"Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. "
                f"Un parking est à votre disposition sur place. À demain."
            )
            envoyer_sms(row["telephone"], msg)
            with open(HISTORIQUE_SMS, "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([row["nom_client"], row["telephone"], row["date_arrivee"].date(), date.today()])

# 🧾 PDF MULTI-LIGNE
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        lignes = [texte[i:i+largeur_max] for i in range(0, len(texte), largeur_max)]
        for ligne in lignes:
            pdf.multi_cell(0, 8, ligne)
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

# 📥 CHARGER DONNÉES
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["nuitees"] = ((pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days).astype(int)
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

# ➕ AJOUTER
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

# ✏️ MODIFIER / SUPPRIMER
def modifier_reservation(df):
    st.subheader("✏️ Modifier / Supprimer")
    df["identifiant"] = df["nom_client"] + " | " + pd.to_datetime(df["date_arrivee"]).astype(str)
    selection = st.selectbox("Choisissez une réservation", df["identifiant"])
    i = df[df["identifiant"] == selection].index[0]
    with st.form("modif"):
        nom = st.text_input("Nom", df.at[i, "nom_client"])
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(df.at[i, "plateforme"]))
        tel = st.text_input("Téléphone", df.at[i, "telephone"])
        arrivee = st.date_input("Arrivée", df.at[i, "date_arrivee"])
        depart = st.date_input("Départ", df.at[i, "date_depart"])
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

# 🗓️ CALENDRIER
def afficher_calendrier(df):
    st.subheader("📅 Calendrier")
    col1, col2 = st.columns(2)
    with col1:
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    with col2:
        annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    nb_jours = calendar.monthrange(annee, mois_index)[1]
    jours = [date(annee, mois_index, i+1) for i in range(nb_jours)]
    planning = {jour: [] for jour in jours}
    couleurs = {"Booking": "🟦", "Airbnb": "🟩", "Autre": "🟧"}
    for _, row in df.iterrows():
        debut = row["date_arrivee"]
        fin = row["date_depart"]
        for jour in jours:
            if debut <= jour < fin:
                icone = couleurs.get(row["plateforme"], "⬜")
                planning[jour].append(f"{icone} {row['nom_client']}")
    table = []
    for semaine in calendar.monthcalendar(annee, mois_index):
        ligne = []
        for jour in semaine:
            if jour == 0:
                ligne.append("")
            else:
                jour_date = date(annee, mois_index, jour)
                contenu = f"{jour}\n" + "\n".join(planning[jour_date])
                ligne.append(contenu)
        table.append(ligne)
    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 📊 RAPPORT MENSUEL
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

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune donnée pour cette période.")

# 📋 LISTE CLIENTS
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%"]
    data = data[colonnes]
    total = data[["nuitees", "prix_brut", "prix_net", "charges"]].sum(numeric_only=True)
    moyenne = data["%"].mean()
    st.dataframe(data)
    st.markdown(f"**Total nuitées :** {int(total['nuitees'])}  |  **Total brut :** {total['prix_brut']:.2f}€  |  **Total net :** {total['prix_net']:.2f}€  |  **Charges :** {total['charges']:.2f}€  |  **% moyen :** {moyenne:.2f}%")

# 🕓 HISTORIQUE SMS
def afficher_historique_sms():
    st.subheader("📨 Historique des SMS envoyés")
    if os.path.exists(HISTORIQUE_SMS):
        df_sms = pd.read_csv(HISTORIQUE_SMS)
        st.dataframe(df_sms)
    else:
        st.info("Aucun SMS envoyé pour le moment.")

# ▶️ MAIN APP
def main():
    df = charger_donnees()
    notifier_arrivees_prochaines(df)

    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📋 Liste Clients", "📨 Historique SMS"])

    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)
    elif onglet == "📋 Liste Clients":
        liste_clients(df)
    elif onglet == "📨 Historique SMS":
        afficher_historique_sms()

if __name__ == "__main__":
    main()