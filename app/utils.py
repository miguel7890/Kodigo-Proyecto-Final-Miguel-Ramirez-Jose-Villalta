from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).parent
API_URL_DEFECTO = "https://SU-API.onrender.com"


@st.cache_data
def leer_csv(nombre, **kwargs):
    return pd.read_csv(DATA / nombre, **kwargs)


def leer_texto(nombre):
    return (DATA / nombre).read_text(encoding="utf-8")


def url_api():
    try:
        defecto = st.secrets.get("API_URL", API_URL_DEFECTO)
    except Exception:
        defecto = API_URL_DEFECTO
    if "api_url" not in st.session_state:
        st.session_state["api_url"] = defecto
    return st.sidebar.text_input("URL de la API", key="api_url").rstrip("/")
