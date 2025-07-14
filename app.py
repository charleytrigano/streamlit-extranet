import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Calendrier des réservations", layout="wide")

st.title("📅 Calendrier des réservations")
st.write("Visualisez vos réservations Airbnb, Booking et autres avec un code couleur par plateforme.")

# Chargement du fichier CSV
csv_file = st.file_uploader("Importer le fichier reservations.csv", type="csv")

if csv_file:
    df = pd.read_csv(csv_file, sep=";")
    
    # Vérification des colonnes attendues
    required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme"}
    if not required_cols.issubset(df.columns):
        st.error("❌ Le fichier CSV doit contenir les colonnes : nom_client, date_arrivee, date_depart, plateforme")
    else:
        # Conversion des dates
        df['date_arrivee'] = pd.to_datetime(df['date_arrivee'])
        df['date_depart'] = pd.to_datetime(df['date_depart'])
        df['duree'] = (df['date_depart'] - df['date_arrivee']).dt.days

        # Dupliquer les lignes pour chaque jour de la réservation
        expanded_rows = []
        for _, row in df.iterrows():
            for i in range(row['duree']):
                new_date = row['date_arrivee'] + pd.Timedelta(days=i)
                expanded_rows.append({
                    "nom_client": row["nom_client"],
                    "date": new_date,
                    "plateforme": row["plateforme"]
                })
        calendar_df = pd.DataFrame(expanded_rows)

        # Affichage avec Plotly
        fig = px.timeline(calendar_df,
                          x_start="date",
                          x_end="date",
                          y="nom_client",
                          color="plateforme",
                          title="Réservations par jour et par client",
                          labels={"date": "Date", "nom_client": "Client", "plateforme": "Plateforme"})
        fig.update_yaxes(autorange="reversed")  # pour afficher du haut vers le bas
        fig.update_layout(height=600)

        st.plotly_chart(fig, use_container_width=True)
