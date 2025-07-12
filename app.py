import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Données Airbnb & Booking", layout="centered")

st.title("🏨 Récupération des données Airbnb & Booking")

st.write("Cette application extrait des données publiques depuis des pages Airbnb ou Booking.")

plateforme = st.radio("Choisissez une plateforme :", ["Airbnb", "Booking"])
url = st.text_input("Entrez l'URL d'une annonce publique :")

def get_booking_data(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string if soup.title else "Titre non trouvé"
        return {
            "Titre": title,
            "URL": url,
            "Plateforme": "Booking"
        }
    except Exception as e:
        return {"Erreur": str(e)}

def get_airbnb_data(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string if soup.title else "Titre non trouvé"
        return {
            "Titre": title,
            "URL": url,
            "Plateforme": "Airbnb"
        }
    except Exception as e:
        return {"Erreur": str(e)}

if st.button("🔎 Extraire les données"):
    if url:
        if "booking" in url.lower():
            result = get_booking_data(url)
        elif "airbnb" in url.lower():
            result = get_airbnb_data(url)
        else:
            result = {"Erreur": "URL non reconnue. Vérifiez qu'il s'agit bien d'un lien Airbnb ou Booking."}
        st.write("### Résultat :")
        st.json(result)
    else:
        st.warning("Veuillez saisir une URL.")

