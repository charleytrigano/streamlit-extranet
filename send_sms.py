import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
from send_sms import envoyer_sms
import os

FICHIER = "reservations.xlsx"
SMS_LOG = "historique_sms.csv"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        mots = texte.split()
        ligne = ""
        for mot in mots:
            if len(ligne + " " + mot) > largeur_max:
                pdf.multi_cell(0, 8, ligne)
                ligne = mot
            else:
                ligne += " " + mot
        if ligne:
            pdf.multi_cell(0, 8, ligne)
    except Exception:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["