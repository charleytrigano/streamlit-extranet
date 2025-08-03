import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import requests
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()

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

# 📩 Envoi SMS + email
def envoyer_sms_et_email(df):
    demain = date.today() + timedelta(days=1)
    df_sms = df[df["date_arrivee"].dt.date == demain]

    logs = []

    for _, row in df_sms.iterrows():
        nom = row["nom_client"]
        tel = row["telephone"]
        plateforme = row.get("plateforme", "Inconnue")
        message = (
            f"Bonjour {nom},\n"
            f"Nous sommes heureux de vous accueillir demain à Nice via {plateforme}.\n"
            "Un emplacement de parking est à votre disposition.\n"
            "Merci de nous indiquer votre heure approximative d’arrivée.\n"
            "Bon voyage et à demain !\n"
            "Annick & Charley"
        )

        # SMS (Free Mobile)
        numeros = os.getenv("NUMERO_DESTINATAIRE", "").split(",")
        api_keys = [os.getenv("FREE_API_KEY_1"), os.getenv("FREE_API_KEY_2")]

        for num, key in zip(numeros, api_keys):
            if key:
                try:
                    url = f"https://smsapi.free-mobile.fr/sendmsg?user={os.getenv('FREE_USER')}&pass={key}&msg={message}"
                    response = requests.get(url)
                    logs.append(f"✅ SMS envoyé à {num.strip()}: {response.status_code}")
                except Exception as e:
                    logs.append(f"❌ Erreur SMS {num.strip()}: {e}")

        # E-mail
        try:
            email_text = f"{message}\n\nClient: {nom}\nPlateforme: {plateforme}\nTel: {tel}"
            msg = MIMEText(email_text)
            msg["Subject"] = f"📩 Réservation pour {nom} - {demain.strftime('%d/%m/%Y')}"
            msg["From"] = os.getenv("EMAIL_FROM")
            msg["To"] = ", ".join(os.getenv("EMAIL_TO", "").split(","))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_PASSWORD"))
                server.sendmail(msg["From"], msg["To"].split(","), msg.as_string())
                logs.append(f"📧 Email envoyé à {msg['To']}")
        except Exception as e:
            logs.append(f"❌ Erreur email: {e}")

    if logs:
        with open("sms_email_log.txt", "a", encoding="utf-8") as f:
            f.write("\n".join(logs) + "\n")

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

# 📅 Calendrier
def afficher_calendrier(df):
    st.subheader("📅 Calendrier des réservations")
    col1, col2 = st.columns(2)
    with col1:
        mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    with col2:
        annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    date_actuelle = date(annee, mois_index, 1)
    nb_jours = calendar.monthrange(annee, mois_index)[1]
    jours = [date_actuelle + timedelta(days=i) for i in range(nb_jours)]
    planning = {jour: [] for jour in jours}
    couleurs = {"Booking": "lightblue", "Airbnb": "lightgreen", "Autre": "orange"}

    for _, row in df.iterrows():
        debut = row["date_arrivee"].date()
        fin = row["date_depart"].date()
        for jour in jours:
            if debut <= jour < fin:
                couleur = couleurs.get(row["plateforme"], "grey")
                planning[jour].append((row["nom_client"], couleur))

    table = []
    for semaine in calendar.monthcalendar(annee, mois_index):
        ligne = []
        for jour in semaine:
            if jour == 0:
                ligne.append("")
            else:
                jour_date = date(annee, mois_index, jour)
                contenu = f"{jour}"
                for nom, color in planning[jour_date]:
                    icone = {"lightblue": "🟦", "lightgreen": "🟩", "orange": "🟧"}.get(color, "⬜")
                    contenu += f"\n{icone} {nom}"
                ligne.append(contenu)
        table.append(ligne)
    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 📊 Rapport avec tableaux + graphiques
def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")

    mois = st.selectbox("Filtre mois", ["Tous"] + sorted(df["mois"].dropna().unique()))
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    data = df[df["annee"] == annee]

    if mois != "Tous":
        data = data[data["mois"] == mois]

    if data.empty:
        st.info("Aucune donnée disponible")
        return

    reg = data.groupby(["annee", "mois", "plateforme"]).agg({
        "prix_brut": "sum",
        "prix_net": "sum",
        "charges": "sum",
        "%": "mean",
        "nuitees": "sum"
    }).reset_index()
    reg["mois_nom"] = reg["mois"].apply(lambda x: calendar.month_name[int(x)] if x != "Tous" else x)
    st.write("### 📅 Sous-totaux par mois et plateforme")
    st.dataframe(reg.style.format({
        "prix_brut": "€{:.2f}", "prix_net": "€{:.2f}",
        "charges": "€{:.2f}", "%": "{:.2f}%", "nuitees": "{:.0f}"
    }))

    st.write("### 📆 Totaux annuels par plateforme")
    totaux = data.groupby(["annee", "plateforme"]).agg({
        "prix_brut": "sum",
        "prix_net": "sum",
        "charges": "sum",
        "%": "mean",
        "nuitees": "sum"
    }).reset_index()
    st.dataframe(totaux.style.format({
        "prix_brut": "€{:.2f}", "prix_net": "€{:.2f}",
        "charges": "€{:.2f}", "%": "{:.2f}%", "nuitees": "{:.0f}"
    }))

    # 📈 Graphiques
    st.write("### 📈 Nuitées par mois et plateforme")
    fig1, ax1 = plt.subplots()
    data.pivot_table(index="mois", columns="plateforme", values="nuitees", aggfunc="sum").fillna(0).sort_index().plot(kind="bar", ax=ax1)
    ax1.set_ylabel("Nuitées")
    st.pyplot(fig1)

    st.write("### 💶 Total net par mois et plateforme")
    fig2, ax2 = plt.subplots()
    data.pivot_table(index="mois", columns="plateforme", values="prix_net", aggfunc="sum").fillna(0).sort_index().plot(kind="bar", ax=ax2)
    ax2.set_ylabel("Prix net (€)")
    st.pyplot(fig2)

# 🚀 Lancement de l'app
if __name__ == "__main__":
    df = charger_donnees()
    envoyer_sms_et_email(df)

    onglet = st.sidebar.radio("Navigation", [
        "📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport"
    ])

    if onglet == "📋 Réservations":
        st.title("📋 Tableau des réservations")
        st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))
    elif onglet == "➕ Ajouter":
        df = ajouter_reservation(df)
    elif onglet == "✏️ Modifier / Supprimer":
        df = modifier_reservation(df)
    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)