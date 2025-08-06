import streamlit as st
import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

FICHIER = "reservations.xlsx"

# 📋 Réservations
def afficher_reservations(df):
    st.title("📋 Réservations")
    st.dataframe(df.drop(columns=["identifiant"], errors="ignore"))

# ➕ Ajouter réservation
def ajouter_reservation(df):
    st.subheader("➕ Nouvelle Réservation")
    with st.form("ajout"):
        nom = st.text_input("Nom")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        tel = st.text_input("Téléphone")
        arrivee = st.date_input("Date arrivée")
        depart = st.date_input("Date départ", min_value=arrivee + timedelta(days=1))
        col1, col2 = st.columns(2)
        with col1:
            prix_brut = st.number_input("Prix brut", min_value=0.0, key="prix_brut_ajout")
        with col2:
            prix_net = st.number_input("Prix net", min_value=0.0, key="prix_net_ajout")

        submit = st.form_submit_button("Enregistrer")
        if submit:
            if prix_net > prix_brut:
                st.error("Le prix net ne peut pas être supérieur au prix brut.")
            else:
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
            if net > brut:
                st.error("Le prix net ne peut pas être supérieur au prix brut.")
            else:
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

# 📊 Rapport (placeholder)
def afficher_rapport(df):
    st.subheader("📊 Rapport")
    st.info("Les statistiques arrivent bientôt !")

# 👥 Liste des clients
def liste_clients(df):
    st.subheader("📄 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()), key="annee_clients")
    mois = st.selectbox("Mois", ["Tous"] + list(range(1, 13)), key="mois_clients")
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]

    if not data.empty:
        data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees", "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit"]
        st.dataframe(data[colonnes])
        st.download_button("📥 Télécharger en Excel", data=data[colonnes].to_csv(index=False).encode("utf-8"), file_name="liste_clients.csv", mime="text/csv")
    else:
        st.info("Aucune donnée pour cette période.")
