import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
from io import BytesIO
import unicodedata
import requests

FICHIER = "reservations.xlsx"
SMS_LOG = "sms_log.csv"
USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
NUM_ADMIN = "+33617722379"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days.astype(int)
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

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

def modifier_reservation(df):
    st.subheader("✏️ Modifier / Supprimer")
    df["identifiant"] = df["nom_client"] + " | " + pd.to_datetime(df["date_arrivee"]).dt.strftime('%Y-%m-%d')
    selection = st.selectbox("Choisissez une réservation", df["identifiant"])
    i = df[df["identifiant"] == selection].index[0]
    with st.form("modif"):
        nom = st.text_input("Nom", df.at[i, "nom_client"])
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(df.at[i, "plateforme"]))
        tel = st.text_input("Téléphone", df.at[i, "telephone"])
        arrivee = st.date_input("Arrivée", pd.to_datetime(df.at[i, "date_arrivee"]))
        depart = st.date_input("Départ", pd.to_datetime(df.at[i, "date_depart"]))
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

def afficher_calendrier(df):
    st.subheader("📅 Calendrier")
    col1, col2 = st.columns(2)
    with col1:
        annee = st.selectbox("Année", sorted(df["annee"].unique()))
    with col2:
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
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

def liste_clients(df):
    st.subheader("📄 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    data = data[["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%"]]
    data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    total = data[["nuitees", "prix_brut", "prix_net", "charges"]].sum().to_dict()
    st.dataframe(data)
    st.markdown(f"**Total nuitées**: {int(total['nuitees'])} | **Total brut**: {total['prix_brut']}€ | **Total net**: {total['prix_net']}€ | **Total charges**: {total['charges']}€")

    # Téléchargement Excel
    buffer = BytesIO()
    data.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("📥 Télécharger Excel", data=buffer, file_name="liste_clients.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def envoyer_sms(numero, message):
    url = "https://smsapi.free-mobile.fr/sendmsg"
    params = {"user": USER, "pass": API_KEY, "msg": message}
    try:
        requests.get(url, params=params)
        return True
    except Exception as e:
        return False

def notifier_arrivees_prochaines(df):
    demain = date.today() + timedelta(days=1)
    df_notif = df[df["date_arrivee"] == demain]
    historique = []

    for _, row in df_notif.iterrows():
        message = f"VILLA TOBIAS - {row['plateforme']}\nBonjour {row['nom_client']}. Votre séjour est prévu du {row['date_arrivee']} au {row['date_depart']}. Afin de vous accueillir merci de nous confirmer votre heure d’arrivée. Un parking est à votre disposition sur place. À demain"
        envoyer_sms(NUM_ADMIN, message)
        historique.append({"nom_client": row["nom_client"], "date": str(datetime.now()), "message": message})

    if historique:
        df_log = pd.DataFrame(historique)
        if os.path.exists(SMS_LOG):
            df_exist = pd.read_csv(SMS_LOG)
            df_log = pd.concat([df_exist, df_log], ignore_index=True)
        df_log.to_csv(SMS_LOG, index=False)

def afficher_historique_sms():
    st.subheader("📨 Historique des SMS")
    if os.path.exists(SMS_LOG):
        df = pd.read_csv(SMS_LOG)
        st.dataframe(df)
    else:
        st.info("Aucun SMS envoyé pour le moment.")

def main():
    st.set_page_config(layout="wide")
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📄 Liste clients", "📨 Historique SMS"])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df)
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📄 Liste clients":
        liste_clients(df)
    elif onglet == "📨 Historique SMS":
        afficher_historique_sms()

    # Envoi automatique
    notifier_arrivees_prochaines(df)

if __name__ == "__main__":
    main()