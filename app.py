import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import requests
from io import BytesIO

FICHIER = "reservations.xlsx"

# 📦 Fonction pour charger les données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce")
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce")
    df["charges"] = df["prix_brut"] - df["prix_net"]
    df["%"] = (df["charges"] / df["prix_brut"] * 100).round(2)
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    df["annee"] = df["date_arrivee"].dt.year
    df["mois"] = df["date_arrivee"].dt.month
    return df

# 📩 SMS automatique
def envoyer_sms_jour(df):
    demain = date.today() + timedelta(days=1)
    if "telephone" not in df.columns or df["telephone"].isnull().all():
        return
    df_sms = df[df["date_arrivee"].dt.date == demain]
    for _, row in df_sms.iterrows():
        message = (
            f"Bonjour {row['nom_client']},\n"
            "Nous sommes heureux de vous accueillir demain à Nice.\n"
            "Un emplacement de parking est à votre disposition.\n"
            "Merci de nous indiquer votre heure approximative d’arrivée.\n"
            "Bon voyage et à demain !\n"
            "Annick & Charley"
        )
        try:
            requests.get(
                f"https://smsapi.free-mobile.fr/sendmsg?user=12026027&pass=1Pat6vSRCLiSXl&msg={message}"
            )
        except:
            pass

# 📅 Afficher calendrier
def afficher_calendrier(df):
    st.subheader("📅 Calendrier des réservations")
    mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    mois_index = list(calendar.month_name).index(mois_nom)
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    date_actuelle = date(annee, mois_index, 1)
    nb_jours = calendar.monthrange(annee, mois_index)[1]

    jours = [date_actuelle + timedelta(days=i) for i in range(nb_jours)]
    planning = {jour: [] for jour in jours}

    couleurs = {
        "Booking": "lightblue",
        "Airbnb": "lightgreen",
        "Autre": "orange"
    }

    for _, row in df.iterrows():
        debut = row["date_arrivee"].date() if pd.notna(row["date_arrivee"]) else None
        fin = row["date_depart"].date() if pd.notna(row["date_depart"]) else None
        if debut and fin:
            for jour in jours:
                if pd.notna(debut) and pd.notna(fin) and debut <= jour < fin:
                    couleur = couleurs.get(row["plateforme"], "lightgrey")
                    planning[jour].append((row["nom_client"], couleur))

    # 📋 Affichage tableau
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
                    contenu += f"\n🟦 {nom}" if color == "lightblue" else f"\n🟩 {nom}" if color == "lightgreen" else f"\n🟧 {nom}"
                ligne.append(contenu)
        table.append(ligne)

    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 📝 Ajouter une réservation
def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajouter"):
        nom = st.text_input("Nom client")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        telephone = st.text_input("Téléphone")
        arrivee = st.date_input("Date d’arrivée")
        depart = st.date_input("Date de départ", min_value=arrivee + timedelta(days=1))
        prix_brut = st.number_input("Prix brut", min_value=0.0)
        prix_net = st.number_input("Prix net", min_value=0.0, max_value=prix_brut)
        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            charges = prix_brut - prix_net
            pourcent = (charges / prix_brut * 100) if prix_brut else 0
            nuitees = (depart - arrivee).days
            nouvelle = {
                "nom_client": nom,
                "plateforme": plateforme,
                "telephone": telephone,
                "date_arrivee": arrivee,
                "date_depart": depart,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": round(pourcent, 2),
                "nuitees": nuitees,
                "annee": arrivee.year,
                "mois": arrivee.month
            }
            df = pd.concat([df, pd.DataFrame([nouvelle])], ignore_index=True)
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation ajoutée")
    return df

# ✏️ Modifier / supprimer
def modifier_reservation(df):
    st.subheader("✏️ Modifier ou Supprimer une Réservation")
    df = df[df["date_arrivee"].notna()]
df["identifiant"] = df["nom_client"] + " | " + df["date_arrivee"].dt.strftime("%Y-%m-%d")

    choix = st.selectbox("Choisissez une réservation", df["identifiant"])
    selection = df[df["identifiant"] == choix].index[0]

    with st.form("modifier"):
        nom = st.text_input("Nom", df.at[selection, "nom_client"])
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"], index=["Booking", "Airbnb", "Autre"].index(df.at[selection, "plateforme"]))
        tel = st.text_input("Téléphone", df.at[selection, "telephone"])
        arrivee = st.date_input("Arrivée", df.at[selection, "date_arrivee"].date())
        depart = st.date_input("Départ", df.at[selection, "date_depart"].date())
        prix_brut = st.number_input("Prix brut", value=float(df.at[selection, "prix_brut"]))
        prix_net = st.number_input("Prix net", value=float(df.at[selection, "prix_net"]))
        submit = st.form_submit_button("Modifier")
        supprimer = st.form_submit_button("🗑 Supprimer")

        if submit:
            df.at[selection, "nom_client"] = nom
            df.at[selection, "plateforme"] = plateforme
            df.at[selection, "telephone"] = tel
            df.at[selection, "date_arrivee"] = arrivee
            df.at[selection, "date_depart"] = depart
            df.at[selection, "prix_brut"] = prix_brut
            df.at[selection, "prix_net"] = prix_net
            df.at[selection, "charges"] = prix_brut - prix_net
            df.at[selection, "%"] = round((prix_brut - prix_net) / prix_brut * 100, 2) if prix_brut else 0
            df.at[selection, "nuitees"] = (depart - arrivee).days
            df.at[selection, "annee"] = arrivee.year
            df.at[selection, "mois"] = arrivee.month
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation modifiée")

        if supprimer:
            df.drop(index=selection, inplace=True)
            df.to_excel(FICHIER, index=False)
            st.warning("🗑 Réservation supprimée")
    return df

# 📊 Rapport mensuel
def rapport_mensuel(df):
    st.subheader("📈 Rapport mensuel")
    mois = st.selectbox("Filtrer par mois", ["Tous"] + sorted(df["mois"].dropna().unique()))
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    df_filtre = df[df["annee"] == annee]
    if mois != "Tous":
        df_filtre = df_filtre[df_filtre["mois"] == mois]

    if not df_filtre.empty:
        regroupement = df_filtre.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum",
            "prix_net": "sum",
            "charges": "sum",
            "%": "mean",
            "nuitees": "sum"
        }).reset_index()
        regroupement["mois"] = regroupement["mois"].apply(lambda x: calendar.month_name[int(x)])
        st.dataframe(regroupement.style.format({
            "prix_brut": "€{:.2f}", "prix_net": "€{:.2f}", "charges": "€{:.2f}", "%": "{:.2f}%", "nuitees": "{:.0f}"
        }))
    else:
        st.info("Aucune donnée pour cette période")

# 🚀 Main
if __name__ == "__main__":
    df = charger_donnees()
    envoyer_sms_jour(df)

    onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport"])

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
