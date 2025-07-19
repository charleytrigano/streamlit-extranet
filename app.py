# ... (début du code identique jusqu'à main)

def afficher_calendrier(df):
    st.subheader("📅 Calendrier mensuel")

    mois = st.selectbox("Mois", list(calendar.month_name)[1:], index=datetime.now().month - 1)
    annee = st.selectbox("Année", list(range(2024, 2027)), index=1)
    plateforme_filtre = st.selectbox("Plateforme", ["Toutes"] + df["plateforme"].unique().tolist())

    mois_index = list(calendar.month_name).index(mois)
    df = df[(df["date_arrivee"].dt.month == mois_index) & (df["date_arrivee"].dt.year == annee)]

    if plateforme_filtre != "Toutes":
        df = df[df["plateforme"] == plateforme_filtre]

    grille = [["" for _ in range(7)] for _ in range(6)]
    premier_jour = datetime(annee, mois_index, 1)
    decalage = premier_jour.weekday()

    jours_dans_mois = calendar.monthrange(annee, mois_index)[1]
    jour = 1
    for ligne in range(6):
        for col in range(7):
            if ligne == 0 and col < decalage:
                continue
            if jour > jours_dans_mois:
                break
            date_jour = datetime(annee, mois_index, jour)
            cellule = ""
            for _, row in df.iterrows():
                if pd.isna(row["date_arrivee"]) or pd.isna(row["date_depart"]):
                    continue
                debut = row["date_arrivee"]
                fin = row["date_depart"]
                if debut <= date_jour < fin:
                    couleur = {
                        "Airbnb": "#a3c9a8",
                        "Booking": "#f4b6c2",
                        "Autre": "#f1fa8c"
                    }.get(row["plateforme"], "#cfcfcf")
                    cellule += f"🟩 {row['nom_client']} ({row['plateforme']})\n"
            grille[ligne][col] = cellule if cellule else ""
            jour += 1

    jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    st.write(" | ".join(jours_semaine))
    for semaine in grille:
        st.write(" | ".join(cell if cell else " " for cell in semaine))

def afficher_tableau(df):
    st.subheader("📋 Tableau des réservations")
    for colonne in df.columns:
        st.text_input(f"🔍 Filtrer par {colonne}", key=f"filter_{colonne}")
    st.dataframe(df)

    # Export
    st.download_button(
        label="📥 Télécharger les réservations",
        data=convert_to_excel(df),
        file_name="reservations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def convert_to_excel(df):
    import io
    from pandas import ExcelWriter

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Réservations")
    output.seek(0)
    return output

# ... reste du code identique


