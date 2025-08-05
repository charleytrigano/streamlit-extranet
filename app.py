import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import requests
import os

FICHIER = "reservations.xlsx"
HISTORIQUE_SMS = "historique_sms.csv"

# 🔤 Nettoyer accents
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 📤 Envoi de SMS via l’API Free
def envoyer_sms_free(message):
    USER = "12026027"
    API_KEY = "MF7Qjs3C8KxKHz"
    DESTINATAIRE = "+33617722379"
    url = "https://smsapi.free-mobile.fr/sendmsg"
    params = {
        "user": USER,
        "pass": API_KEY,
        "msg": message
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return True
    except Exception:
        pass
    return False

# 🕐 Notification automatique
def notifier_arrivees_prochaines(df):
    if "date_arrivee" not in df:
        return
    if not pd.api.types.is_datetime64_any_dtype(df["date_arrivee"]):
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    demain = (date.today() + timedelta(days=1))
    df_notif = df[df["date_arrivee"].dt.date == demain]
    for _, row in df_notif.iterrows():
        message = f"{row['plateforme']} - {row['nom_client']} - {row['date_arrivee'].date()} - {row['date_depart'].date()}"
        if envoyer_sms_free(message):
            log = {"date": datetime.now(), "client": row["nom_client"], "message": message}
            historique = pd.DataFrame([log])
            if os.path.exists(HISTORIQUE_SMS):
                historique.to_csv(HISTORIQUE_SMS, mode="a", header=False, index=False)
            else:
                historique.to_csv(HISTORIQUE_SMS, index=False)

# 🧾 Écriture PDF sécurisée
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        mots = texte.split()
        ligne = ""
        for mot in mots:
            if pdf.get_string_width(ligne + " " + mot) < largeur_max:
                ligne += " " + mot
            else:
                pdf.multi_cell(0, 8, ligne.strip())
                ligne = mot
        if ligne:
            pdf.multi_cell(0, 8, ligne.strip())
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

# 📥 Charger données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
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

# ✏️ Modifier réservation
def modifier_reservation(df):
    st.subheader("✏️ Modifier / Supprimer")
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

# 📅 Calendrier
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
        debut = row["date_arrivee"].date()
        fin = row["date_depart"].date()
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

# 📋 Liste clients
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois = st.selectbox("Mois", ["Tous"] + list(range(1, 13)))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).round(2)
        data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).round(2)
        colonnes = ["nom_client", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit"]
        st.dataframe(data[colonnes])

        total = data[colonnes[3:]].sum(numeric_only=True).to_frame().T
        total.index = ["Total"]
        st.dataframe(total)

        # Excel export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            data[colonnes].to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"liste_clients_{annee}_{mois}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune donnée disponible.")

# 📨 Historique des SMS
def afficher_historique_sms():
    st.subheader("📨 Historique des SMS envoyés")
    if os.path.exists(HISTORIQUE_SMS):
        historique = pd.read_csv(HISTORIQUE_SMS, parse_dates=["date"])
        st.dataframe(historique.sort_values("date", ascending=False))
    else:
        st.info("Aucun SMS envoyé pour l’instant.")

# ▶️ App
def main():
    st.set_page_config(layout="wide")
    df = charger_donnees()
    notifier_arrivees_prochaines(df)
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📋 Liste clients", "📨 Historique SMS"])

    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📋 Liste clients":
        liste_clients(df)
    elif onglet == "📨 Historique SMS":
        afficher_historique_sms()
    elif onglet == "📊 Rapport":
        st.write("Rapport désactivé temporairement (PDF non utilisé).")

if __name__ == "__main__":
    main()