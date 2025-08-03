import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import os
from io import BytesIO

FICHIER = "reservations.xlsx"

def charger_donnees():
    if not os.path.exists(FICHIER):
        return pd.DataFrame(columns=[
            "nom_client", "plateforme", "telephone", "date_arrivee", "date_depart",
            "prix_brut", "prix_net", "charges", "%", "nuitees", "annee", "mois"
        ])
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

def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajout"):
        nom = st.text_input("Nom")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        tel = st.text_input("Téléphone")
        arrivee = st.date_input("Date arrivée")
        depart = st.date_input("Date départ", min_value=arrivee + timedelta(days=1))
        prix_brut = st.number_input("Prix brut", min_value=0.0, step=10.0)
        prix_net = st.number_input("Prix net", min_value=0.0, max_value=prix_brut, step=10.0)

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
        net = st.number_input("Prix net", value=float(df.at[i, "prix_net"]), max_value=brut)

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
                contenu = f"{jour}"
                for ligne_client in planning[jour_date]:
                    contenu += f"\n{ligne_client}"
                ligne.append(contenu)
        table.append(ligne)

    st.table(pd.DataFrame(table, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

def rapport(df):
    st.subheader("📊 Rapport détaillé")

    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df["mois"].unique()))
    plateforme = st.selectbox("Plateforme", ["Toutes"] + sorted(df["plateforme"].unique()))

    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if plateforme != "Toutes":
        data = data[data["plateforme"] == plateforme]

    if not data.empty:
        st.write("### 🔹 Données filtrées")
        st.dataframe(data)

        reg = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum", "prix_net": "sum", "charges": "sum",
            "%": "mean", "nuitees": "sum"
        }).reset_index()

        reg["mois"] = reg["mois"].apply(lambda x: calendar.month_name[int(x)])
        st.write("### 🔢 Sous-totaux")
        st.dataframe(reg)

        moyennes = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": lambda x: (x.sum() / data["nuitees"].sum()),
            "prix_net": lambda x: (x.sum() / data["nuitees"].sum())
        }).reset_index()
        moyennes.rename(columns={"prix_brut": "Brut/nuitée", "prix_net": "Net/nuitée"}, inplace=True)

        st.write("### 💡 Moyennes par nuitée")
        st.dataframe(moyennes)

        total_annee = df[df["annee"] == annee].groupby("plateforme")[["prix_brut", "prix_net", "nuitees"]].sum().reset_index()
        st.write("### 📌 Totaux annuels par plateforme")
        st.dataframe(total_annee)

        with BytesIO() as b:
            df_excel = data.copy()
            df_excel.to_excel(b, index=False)
            st.download_button("📥 Télécharger rapport Excel", data=b.getvalue(), file_name="rapport_filtré.xlsx")

    else:
        st.info("Aucune donnée disponible pour ce filtre.")

# 🚀 Interface principale
if __name__ == "__main__":
    df = charger_donnees()
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
        rapport(df)