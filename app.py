import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="📅 Extranet Planning", layout="wide")

st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier `.csv` contenant les réservations à venir.")

# Upload CSV
csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        # Lecture avec séparateur ";"
        df = pd.read_excel(csv_file)
        df.columns = df.columns.str.strip().str.lower()  # Nettoyage des noms de colonnes

        # Conversion des colonnes de date
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        # Colonnes requises
        required_cols = {
            "nom_client", "date_arrivee", "date_depart",
            "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"
        }

        if not required_cols.issubset(df.columns):
            st.error("❌ Le fichier doit contenir toutes les colonnes suivantes : " + ", ".join(required_cols))
        else:
            st.success("✅ Données importées avec succès !")
            st.dataframe(df)

            # Affichage d'un résumé financier
            st.markdown("### 💰 Résumé financier")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Prix Brut Total", f"{df['prix_brut'].sum():,.2f} €")
            col2.metric("Prix Net Total", f"{df['prix_net'].sum():,.2f} €")
            col3.metric("Charges moy.", f"{df['charges'].mean():.2f} €")
            col4.metric("Marge Moyenne", f"{df['%'].mean():.1f} %")

    except Exception as e:
        st.error(f"❌ Erreur lors de l'importation du fichier : {e}")

else:
    st.info("Veuillez importer un fichier `.csv` pour continuer.")
