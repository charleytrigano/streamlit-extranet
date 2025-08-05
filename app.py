# app.py

import streamlit as st
import pandas as pd
import calendar
import requests
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import os

FICHIER = "reservations.xlsx"
FICHIER_SMS = "historique_sms.csv"

USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
ADMIN_TEL = "+33617722379"

# 🔤 Nettoyer texte
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 📤 Envoyer SMS
def envoyer_sms(numero, message):
    params = {"user": USER, "pass": API_KEY, "to": numero, "msg": message}
    try:
        r = requests.get("https://smsapi.free-mobile.fr/sendmsg", params=params)
        return r.status_code == 200
    except Exception:
        return False

# ✉️ Enregistrer historique
def enregistrer_sms(nom, telephone, message, date_envoi):
    ligne = pd.DataFrame([{
        "nom": nom,
        "telephone": telephone,
        "message": message,
        "date_envoi": date_envoi.strftime('%Y-%m-%d %H:%M')
    }])
    if os.path.exists(FICHIER_SMS):
        df = pd.read_csv(FICHIER_SMS)
        df = pd.concat([df, ligne], ignore_index=True)
    else:
        df = ligne
    df.to_csv(FICHIER_SMS, index=False)

# 🧾 Écrire texte découpé PDF
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        mots = texte.split()
        ligne = ""
        for mot in mots:
            test = ligne + " " + mot if ligne else mot
            if pdf.get_string_width(test) < largeur_max:
                ligne = test
            else:
                pdf.multi_cell(0, 8, ligne)
                ligne = mot
        if ligne:
            pdf.multi_cell(0, 8, ligne)
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

# 📥 Chargement
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

# ✏️ Modifier / supprimer
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

# 🗓️ Calendrier
def afficher_calendrier(df):
    st.subheader("📅 Calendrier")
    col1, col2 = st.columns(2)
    with col1:
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    with col2:
        annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    jours = [date(annee, mois_index, i+1) for i in range(calendar.monthrange(annee, mois_index)[1])]
    planning = {jour: [] for jour in jours}
    couleurs = {"Booking": "🟦", "Airbnb": "🟩", "Autre": "🟧"}
    for _, row in df.iterrows():
        debut, fin = row["date_arrivee"], row["date_depart"]
        for jour in jours:
            if debut <= jour < fin:
                icone = couleurs.get(row["plateforme"], "⬜")
                planning[jour].append(f"{icone} {row['nom_client']}")
    table = []
    for semaine in calendar.monthcalendar(annee, mois_index):
        ligne = []
        for jour in semaine:
            jour_date = date(annee, mois_index, jour) if jour else None
            contenu = f"{jour}\n" + "\n".join(planning[jour_date]) if jour else ""
            ligne.append(contenu)
        table.append(ligne)
    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 🧾 Liste clients
def liste_clients(df):
    st.subheader("📄 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()), key="liste_annee")
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()), key="liste_mois")
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == int(mois)]
    data["prix_moyen_brut"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    data["prix_moyen_net"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_moyen_brut", "prix_moyen_net"]
    st.dataframe(data[colonnes])
    total = data[colonnes].select_dtypes(include='number').sum().to_frame("Total").T
    st.dataframe(total)

    # Export Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        data[colonnes].to_excel(writer, index=False)
        total.to_excel(writer, startrow=len(data)+2, index=False)
    buffer.seek(0)
    st.download_button("📥 Télécharger Excel", data=buffer, file_name="liste_clients.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 📊 Rapport
def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == int(mois)]
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

        # Excel export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ▶️ Lancement
def main():
    st.set_page_config(layout="wide")
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📄 Liste Clients", "📨 Historique SMS"])
    
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        for _, row in df.iterrows():
            st.markdown(f"**{row['nom_client']}** | {row['plateforme']} | {row['date_arrivee']} → {row['date_depart']}")
            if st.button(f"📨 Envoyer SMS à {row['nom_client']}", key=f"sms_{row.name}"):
                message = f"VILLA TOBIAS - {row['plateforme']}\nBonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}. Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. Nous vous rappelons qu’un parking est à votre disposition sur place. À demain."
                if envoyer_sms(row["telephone"], message):
                    enregistrer_sms(row["nom_client"], row["telephone"], message, datetime.now())
                    st.success("✅ SMS envoyé")
                else:
                    st.error("❌ Échec de l’envoi")

    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)
    elif onglet == "📄 Liste Clients":
        liste_clients(df)
    elif onglet == "📨 Historique SMS":
        if os.path.exists(FICHIER_SMS):
            st.subheader("📨 Historique des SMS")
            historique = pd.read_csv(FICHIER_SMS)
            st.dataframe(historique)
        else:
            st.info("Aucun SMS envoyé pour le moment.")

if __name__ == "__main__":
    main()