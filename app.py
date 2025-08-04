import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import textwrap

FICHIER = "reservations.xlsx"

def nettoyer_texte(s):
    if isinstance(s, str):
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
        s = s.replace("\n", " ").strip()
        return s
    return str(s)

def couper_mots_longs(texte, longueur_max=30):
    return ' '.join([mot if len(mot) <= longueur_max else mot[:longueur_max] + '…' for mot in texte.split()])

def ecrire_pdf_multiligne(pdf, texte, largeur_max=160):
    if not isinstance(texte, str) or not texte.strip():
        texte = "-"
    texte = nettoyer_texte(texte)
    texte = couper_mots_longs(texte)
    lignes = textwrap.wrap(texte, width=largeur_max)
    for ligne in lignes:
        try:
            pdf.set_x(pdf.l_margin)
            pdf.cell(0, 8, ligne, ln=1)
        except Exception:
            pdf.cell(0, 8, "[ligne ignorée]", ln=1)

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
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": prix_brut - prix_net,
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

def exporter_pdf(data, annee):
    pdf = FPDF(orientation="L", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, txt=f"Rapport Réservations - {annee}", ln=True, align="C")
    pdf.ln(5)
    for _, row in data.iterrows():
        texte = (
            f"{row['annee']} {row['mois']} | Plateforme: {row['plateforme']} | Nuitées: {row['nuitees']} | "
            f"Brut: {row['prix_brut']}€ | Net: {row['prix_net']}€ | Charges: {row['charges']}€ | "
            f"Moy. brut/nuit: {row['prix_moyen_brut']}€ | Moy. net/nuit: {row['prix_moyen_net']}€"
        )
        ecrire_pdf_multiligne(pdf, texte, largeur_max=160)
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    mois = st.selectbox("Filtre mois", ["Tous"] + sorted(df["mois"].unique()))
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        reg = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum", "prix_net": "sum", "charges": "sum", "%": "mean", "nuitees": "sum"
        }).reset_index()
        reg["prix_moyen_brut"] = (reg["prix_brut"] / reg["nuitees"]).round(2)
        reg["prix_moyen_net"] = (reg["prix_net"] / reg["nuitees"]).round(2)
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

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        pdf_buffer = exporter_pdf(reg, annee)
        st.download_button("📄 Télécharger PDF", data=pdf_buffer, file_name=f"rapport_{annee}.pdf", mime="application/pdf")
    else:
        st.info("Aucune donnée pour cette période.")

def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport"])
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
        rapport_mensuel(df)

if __name__ == "__main__":
    main()