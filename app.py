import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from io import BytesIO
import unicodedata
import requests
import os

FICHIER = "reservations.xlsx"
SMS_HISTO = "sms_historique.csv"

USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUM_DEST = "+33617722379"

# 🔤 Nettoyage texte
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 📥 Chargement données
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

# ➕ Ajout réservation
def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajout"):
        nom = st.text_input("Nom")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        tel = st.text_input("Téléphone")
        arrivee = st.date_input("Date arrivée")
        depart = st.date_input("Date départ", min_value=arrivee + timedelta(days=1))
        brut = st.number_input("Prix brut", min_value=0.0, format="%.2f")
        net = st.number_input("Prix net", min_value=0.0, max_value=brut, format="%.2f")
        submit = st.form_submit_button("Enregistrer")
        if submit:
            ligne = {
                "nom_client": nom,
                "plateforme": plateforme,
                "telephone": tel,
                "date_arrivee": arrivee,
                "date_depart": depart,
                "prix_brut": round(brut, 2),
                "prix_net": round(net, 2),
                "charges": round(brut - net, 2),
                "%": round(((brut - net) / brut * 100) if brut else 0, 2),
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
        arrivee = st.date_input("Date arrivée", df.at[i, "date_arrivee"])
        depart = st.date_input("Date départ", df.at[i, "date_depart"])
        brut = st.number_input("Prix brut", value=float(df.at[i, "prix_brut"]), format="%.2f")
        net = st.number_input("Prix net", value=float(df.at[i, "prix_net"]), format="%.2f")
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
            df.at[i, "%"] = round(((brut - net) / brut * 100) if brut else 0, 2)
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
    mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    nb_jours = calendar.monthrange(annee, mois_index)[1]
    jours = [date(annee, mois_index, i+1) for i in range(nb_jours)]
    planning = {jour: [] for jour in jours}
    couleurs = {"Booking": "🟦", "Airbnb": "🟩", "Autre": "🟧"}
    for _, row in df.iterrows():
        for jour in jours:
            if row["date_arrivee"] <= jour < row["date_depart"]:
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

# 📊 Rapport
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

        # Excel export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune donnée pour cette période.")

# 📋 Liste clients
def liste_clients(df):
    st.subheader("📋 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%"]
    data = data[colonnes]
    data["prix_brut/nuit"] = (df["prix_brut"] / df["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    data["prix_net/nuit"] = (df["prix_net"] / df["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    st.dataframe(data)

# 📨 Historique SMS
def afficher_historique_sms():
    st.subheader("📨 Historique des SMS")
    if os.path.exists(SMS_HISTO):
        sms_df = pd.read_csv(SMS_HISTO)
        st.dataframe(sms_df)
    else:
        st.info("Aucun SMS envoyé pour le moment.")

# 📤 Envoi SMS
def notifier_arrivees_prochaines(df):
    aujourd = date.today()
    demain = aujourd + timedelta(days=1)
    df_notif = df[df["date_arrivee"] == demain]
    sms_envoyes = []
    for _, row in df_notif.iterrows():
        message = (
            f"VILLA TOBIAS - {row['plateforme']}\n"
            f"Bonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}.\n"
            f"Afin de vous accueillir merci de nous confirmer votre heure d’arrivée.\n"
            f"Un parking est à votre disposition sur place. A demain"
        )
        try:
            url = "https://smsapi.free-mobile.fr/sendmsg"
            params = {"user": USER, "pass": API_KEY, "msg": message}
            requests.get(url, params=params)
            sms_envoyes.append({
                "date": aujourd,
                "nom": row["nom_client"],
                "telephone": row["telephone"],
                "message": message
            })
        except:
            pass
    if sms_envoyes:
        pd.DataFrame(sms_envoyes).to_csv(SMS_HISTO, index=False, mode='a', header=not os.path.exists(SMS_HISTO))
        st.success(f"{len(sms_envoyes)} SMS envoyés")

# ▶️ Main
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📋 Liste clients", "📨 Historique SMS"])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
        if st.button("📤 Envoyer les SMS pour demain"):
            notifier_arrivees_prochaines(df)
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)
    elif onglet == "📋 Liste clients":
        liste_clients(df)
    elif onglet == "📨 Historique SMS":
        afficher_historique_sms()

if __name__ == "__main__":
    main()