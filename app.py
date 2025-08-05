import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import calendar
import requests
import os

FICHIER = "reservations.xlsx"
SMS_HISTORIQUE = "historique_sms.csv"

API_USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUMERO_PROPRIETAIRE = "+33617722379"
URL_SMS = "https://smsapi.free-mobile.fr/sendmsg"

# 🔄 Charger les données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).round(2)
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

# 📨 Envoi SMS
def envoyer_sms(msg):
    payload = {"user": API_USER, "pass": API_KEY, "msg": msg}
    r = requests.get(URL_SMS, params=payload)
    return r.status_code == 200

# 📝 Historique CSV
def enregistrer_sms(nom, numero, contenu):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ligne = pd.DataFrame([{
        "Nom client": nom,
        "Téléphone": numero,
        "Contenu": contenu,
        "Date envoi": now
    }])
    if os.path.exists(SMS_HISTORIQUE):
        ligne.to_csv(SMS_HISTORIQUE, mode='a', index=False, header=False)
    else:
        ligne.to_csv(SMS_HISTORIQUE, index=False)

# 📨 Interface SMS
def interface_sms(df):
    st.subheader("📨 SMS à envoyer")
    demain = date.today() + timedelta(days=1)
    clients_demain = df[df["date_arrivee"] == demain]
    if clients_demain.empty:
        st.info("Aucun client n’arrive demain.")
        return
    for _, row in clients_demain.iterrows():
        msg = (
            f"VILLA TOBIAS - {row['plateforme']}\n"
            f"Bonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}."
            f" Afin de vous accueillir merci de nous confirmer votre heure d’arrivée."
            f" Nous vous rappelons qu’un parking est à votre disposition sur place. À demain"
        )
        if st.button(f"Envoyer SMS à {row['nom_client']}"):
            ok = envoyer_sms(msg)
            if ok:
                enregistrer_sms(row['nom_client'], NUMERO_PROPRIETAIRE, msg)
                st.success(f"SMS envoyé à {row['nom_client']}")
            else:
                st.error(f"Erreur lors de l’envoi à {row['nom_client']}")

# 📜 Historique des SMS
def historique_sms():
    st.subheader("📜 Historique des SMS")
    if os.path.exists(SMS_HISTORIQUE):
        histo = pd.read_csv(SMS_HISTORIQUE)
        st.dataframe(histo)
        csv = histo.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger CSV", csv, "historique_sms.csv", "text/csv")
    else:
        st.info("Aucun SMS encore envoyé.")

# ▶️ Lancement
def main():
    st.sidebar.title("Menu")
    choix = st.sidebar.radio("Choisissez :", [
        "📋 Réservations",
        "➕ Ajouter",
        "✏️ Modifier / Supprimer",
        "📅 Calendrier",
        "📊 Rapport",
        "📨 SMS à envoyer",
        "📜 Historique des SMS"
    ])
    df = charger_donnees()

    if choix == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df)

    elif choix == "➕ Ajouter":
        st.title("➕ Ajouter une réservation")
        with st.form("form_ajout"):
            nom = st.text_input("Nom client")
            plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
            tel = st.text_input("Téléphone")
            arrivee = st.date_input("Date d’arrivée", date.today())
            depart = st.date_input("Date de départ", date.today() + timedelta(days=1))
            brut = st.number_input("Prix brut", 0.0)
            net = st.number_input("Prix net", 0.0, brut)
            envoyer = st.form_submit_button("Enregistrer")
            if envoyer:
                ligne = pd.DataFrame([{
                    "nom_client": nom,
                    "plateforme": plateforme,
                    "telephone": tel,
                    "date_arrivee": arrivee,
                    "date_depart": depart,
                    "prix_brut": round(brut, 2),
                    "prix_net": round(net, 2),
                    "charges": round(brut - net, 2),
                    "%": round((brut - net) / brut * 100 if brut else 0, 2),
                    "nuitees": (depart - arrivee).days,
                    "annee": arrivee.year,
                    "mois": arrivee.month
                }])
                df = pd.concat([df, ligne], ignore_index=True)
                df.to_excel(FICHIER, index=False)
                st.success("Réservation enregistrée")

    elif choix == "✏️ Modifier / Supprimer":
        st.title("✏️ Modifier / Supprimer")
        df["identifiant"] = df["nom_client"] + " - " + df["date_arrivee"].astype(str)
        selected = st.selectbox("Sélectionnez", df["identifiant"])
        i = df[df["identifiant"] == selected].index[0]
        with st.form("form_modif"):
            nom = st.text_input("Nom", df.at[i, "nom_client"])
            plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(df.at[i, "plateforme"]))
            tel = st.text_input("Téléphone", df.at[i, "telephone"])
            arrivee = st.date_input("Arrivée", df.at[i, "date_arrivee"])
            depart = st.date_input("Départ", df.at[i, "date_depart"])
            brut = st.number_input("Brut", value=float(df.at[i, "prix_brut"]))
            net = st.number_input("Net", value=float(df.at[i, "prix_net"]))
            modif = st.form_submit_button("Modifier")
            delete = st.form_submit_button("Supprimer")
            if modif:
                df.at[i, "nom_client"] = nom
                df.at[i, "plateforme"] = plateforme
                df.at[i, "telephone"] = tel
                df.at[i, "date_arrivee"] = arrivee
                df.at[i, "date_depart"] = depart
                df.at[i, "prix_brut"] = round(brut, 2)
                df.at[i, "prix_net"] = round(net, 2)
                df.at[i, "charges"] = round(brut - net, 2)
                df.at[i, "%"] = round((brut - net) / brut * 100 if brut else 0, 2)
                df.at[i, "nuitees"] = (depart - arrivee).days
                df.at[i, "annee"] = arrivee.year
                df.at[i, "mois"] = arrivee.month
                df.to_excel(FICHIER, index=False)
                st.success("Réservation modifiée")
            if delete:
                df = df.drop(index=i)
                df.to_excel(FICHIER, index=False)
                st.warning("Réservation supprimée")

    elif choix == "📅 Calendrier":
        st.title("📅 Calendrier")
        mois = st.selectbox("Mois", list(calendar.month_name)[1:])
        annee = st.selectbox("Année", sorted(df["annee"].unique()))
        mois_index = list(calendar.month_name).index(mois)
        nb_jours = calendar.monthrange(annee, mois_index)[1]
        jours = [date(annee, mois_index, j+1) for j in range(nb_jours)]
        planning = {jour: [] for jour in jours}
        for _, row in df.iterrows():
            d1, d2 = row["date_arrivee"], row["date_depart"]
            for jour in jours:
                if d1 <= jour < d2:
                    planning[jour].append(f"{row['plateforme']} - {row['nom_client']}")
        table = []
        for semaine in calendar.monthcalendar(annee, mois_index):
            ligne = []
            for j in semaine:
                if j == 0:
                    ligne.append("")
                else:
                    date_ = date(annee, mois_index, j)
                    texte = f"{j}\n" + "\n".join(planning.get(date_, []))
                    ligne.append(texte)
            table.append(ligne)
        st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

    elif choix == "📊 Rapport":
        st.title("📊 Rapport")
        annee = st.selectbox("Année", sorted(df["annee"].unique()))
        mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
        data = df[df["annee"] == annee]
        if mois != "Tous":
            data = data[data["mois"] == int(mois)]
        if data.empty:
            st.info("Aucune donnée")
        else:
            reg = data.groupby(["annee", "mois", "plateforme"]).agg({
                "prix_brut": "sum",
                "prix_net": "sum",
                "charges": "sum",
                "%": "mean",
                "nuitees": "sum"
            }).reset_index()
            reg["prix_moyen_brut"] = (reg["prix_brut"] / reg["nuitees"]).replace([float('inf'), float('-inf')], 0).fillna(0).round(2)
            reg["prix_moyen_net"] = (reg["prix_net"] / reg["nuitees"]).replace([float('inf'), float('-inf')], 0).fillna(0).round(2)
            reg["%"] = reg["%"].round(2)
            st.dataframe(reg)
            excel = reg.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger Excel", excel, f"rapport_{annee}.csv", "text/csv")

    elif choix == "📨 SMS à envoyer":
        interface_sms(df)

    elif choix == "📜 Historique des SMS":
        historique_sms()

if __name__ == "__main__":
    main()