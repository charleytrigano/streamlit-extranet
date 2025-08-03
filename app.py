# app.py
import streamlit as st
import pandas as pd
import calendar
import matplotlib.pyplot as plt
from datetime import date, timedelta
from io import BytesIO
import os

FICHIER = "reservations.xlsx"

# 🧩 Charger les données
def charger_donnees():
    if os.path.exists(FICHIER):
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
    else:
        df = pd.DataFrame(columns=[
            "plateforme", "nom_client", "date_arrivee", "date_depart", "prix_brut",
            "prix_net", "charges", "%", "nuitees", "annee", "mois", "telephone"
        ])
    return df

def sauvegarder_donnees(df):
    df.to_excel(FICHIER, index=False)

# ➕ Ajouter une réservation
def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajout"):
        nom = st.text_input("Nom du client")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        tel = st.text_input("Téléphone")
        arrivee = st.date_input("Date d'arrivée")
        depart = st.date_input("Date de départ", min_value=arrivee + timedelta(days=1))
        prix_brut = st.number_input("Prix brut", min_value=0.0)
        prix_net = st.number_input("Prix net", min_value=0.0, max_value=prix_brut)
        submit = st.form_submit_button("Enregistrer")
        if submit:
            charges = prix_brut - prix_net
            pourcent = (charges / prix_brut * 100) if prix_brut else 0
            nuitees = (depart - arrivee).days
            ligne = {
                "plateforme": plateforme, "nom_client": nom, "telephone": tel,
                "date_arrivee": arrivee, "date_depart": depart,
                "prix_brut": prix_brut, "prix_net": prix_net,
                "charges": charges, "%": round(pourcent, 2),
                "nuitees": nuitees, "annee": arrivee.year, "mois": arrivee.month
            }
            df = pd.concat([df, pd.DataFrame([ligne])], ignore_index=True)
            sauvegarder_donnees(df)
            st.success("✅ Réservation enregistrée")
    return df

# ✏️ Modifier une réservation
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
            sauvegarder_donnees(df)
            st.success("✅ Réservation modifiée")
        if delete:
            df.drop(index=i, inplace=True)
            sauvegarder_donnees(df)
            st.warning("🗑 Réservation supprimée")
    return df

# 📅 Calendrier
def afficher_calendrier(df):
    st.subheader("📅 Calendrier")
    mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:])
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois_index = list(calendar.month_name).index(mois_nom)
    date_debut = date(annee, mois_index, 1)
    jours = [date_debut + timedelta(days=i) for i in range(calendar.monthrange(annee, mois_index)[1])]
    planning = {jour: [] for jour in jours}
    couleurs = {"Booking": "🟦", "Airbnb": "🟩", "Autre": "🟧"}

    for _, row in df.iterrows():
        for jour in jours:
            if row["date_arrivee"].date() <= jour < row["date_depart"].date():
                icone = couleurs.get(row["plateforme"], "⬜")
                planning[jour].append(f"{icone} {row['nom_client']}")

    tableau = []
    for semaine in calendar.monthcalendar(annee, mois_index):
        ligne = []
        for jour in semaine:
            if jour == 0:
                ligne.append("")
            else:
                jour_date = date(annee, mois_index, jour)
                contenu = f"{jour}\n" + "\n".join(planning[jour_date])
                ligne.append(contenu)
        tableau.append(ligne)

    st.table(pd.DataFrame(tableau, columns=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))

# 📊 Rapport
def rapport(df):
    st.subheader("📊 Rapport détaillé")
    mois = st.selectbox("Filtrer par mois", ["Tous"] + sorted(df["mois"].dropna().unique()))
    annee = st.selectbox("Filtrer par année", sorted(df["annee"].dropna().unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]

    if not data.empty:
        grouped = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum",
            "prix_net": "sum",
            "charges": "sum",
            "%": "mean",
            "nuitees": "sum"
        }).reset_index()

        grouped["prix_moyen_brut"] = (grouped["prix_brut"] / grouped["nuitees"]).round(2)
        grouped["prix_moyen_net"] = (grouped["prix_net"] / grouped["nuitees"]).round(2)
        grouped["mois"] = grouped["mois"].apply(lambda x: calendar.month_name[int(x)])

        st.dataframe(grouped)

        # 📈 Graphiques
        st.markdown("### 📈 Graphiques")
        col1, col2 = st.columns(2)

        with col1:
            fig1, ax1 = plt.subplots()
            for key, g in data.groupby("plateforme"):
                g.groupby("mois")["nuitees"].sum().plot(ax=ax1, label=key)
            ax1.set_title("Nuitées par mois")
            ax1.legend()
            st.pyplot(fig1)

        with col2:
            fig2, ax2 = plt.subplots()
            for key, g in data.groupby("plateforme"):
                g.groupby("mois")["prix_net"].sum().plot(ax=ax2, label=key)
            ax2.set_title("Prix net par mois")
            ax2.legend()
            st.pyplot(fig2)

        # 📤 Export Excel
        buffer = BytesIO()
        grouped.to_excel(buffer, index=False)
        st.download_button("📥 Télécharger rapport Excel", data=buffer.getvalue(), file_name="rapport.xlsx")

        # 📃 Impression
        st.markdown("### 🖨️ État mensuel imprimable")
        st.dataframe(data[[
            "plateforme", "nom_client", "date_arrivee", "date_depart",
            "nuitees", "prix_brut", "prix_net"
        ]])

        st.write("#### 🔢 Sous-totaux par plateforme")
        st.dataframe(
            data.groupby("plateforme")[["prix_brut", "prix_net", "nuitees"]].sum()
        )

        st.write("#### 📅 Totaux annuels par plateforme")
        total_annuel = df[df["annee"] == annee].groupby("plateforme")[["prix_brut", "prix_net", "nuitees"]].sum()
        st.dataframe(total_annuel)
    else:
        st.info("Aucune donnée pour cette période.")

# 🚀 Application principale
df = charger_donnees()
onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport"])

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
    rapport(df)