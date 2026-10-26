import json
import math

import pandas as pd
import requests
import streamlit as st

from utils import leer_csv, url_api

ENTRADAS = [
    "order_id", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date", "estado_cliente", "n_items",
    "n_vendedores", "precio_total", "flete_total", "peso_total_g", "fotos_promedio", "categoria",
    "estado_vendedor", "tipo_pago", "cuotas_max",
]
FECHAS = ENTRADAS[1:6]
OPCIONALES = {"order_approved_at", "order_delivered_carrier_date", "peso_total_g", "fotos_promedio", "categoria"}
ENTEROS = {"n_items", "n_vendedores", "cuotas_max"}
DECIMALES = {"precio_total", "flete_total", "peso_total_g", "fotos_promedio"}


def limpio(v):
    if v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and v.strip() == ""):
        return None
    return v


st.title("Riesgo de mala reseña de un pedido")
st.caption("Probabilidad de que el cliente deje 1 o 2 estrellas, calculada al confirmar la entrega "
           "(sin usar nada de la reseña).")
api = url_api()
st.sidebar.caption("El servidor gratuito de Render se duerme tras 15 min sin uso: la primera llamada puede tardar ~60 s.")

ejemplos = leer_csv("pedidos_ejemplo.csv", dtype={"order_id": str})
eleccion = st.selectbox("Pedido real de ejemplo", ejemplos["descripcion"].tolist())
base = ejemplos.loc[ejemplos["descripcion"] == eleccion].iloc[0]

with st.form("pedido"):
    st.subheader("Datos del pedido (editables)")
    valores = {}
    columnas = st.columns(3)
    for i, campo in enumerate(ENTRADAS):
        actual = limpio(base[campo])
        with columnas[i % 3]:
            etiqueta = campo + (" (opcional)" if campo in OPCIONALES else "")
            if campo in ENTEROS:
                valores[campo] = st.number_input(etiqueta, value=int(actual) if actual is not None else 1, step=1)
            elif campo in DECIMALES:
                texto = st.text_input(etiqueta, value="" if actual is None else str(actual))
                try:
                    valores[campo] = None if texto.strip() == "" else float(texto)
                except ValueError:
                    valores[campo] = texto
            else:
                valores[campo] = limpio(st.text_input(etiqueta, value="" if actual is None else str(actual)))
    enviar = st.form_submit_button("Calcular riesgo", type="primary")

if enviar:
    with st.spinner("Consultando la API de riesgo..."):
        try:
            r = requests.post(f"{api}/riesgo", json=valores, timeout=90)
        except requests.exceptions.RequestException:
            st.warning("No pudimos contactar la API. Si está desplegada en Render (plan gratuito), el servidor puede "
                       "tardar hasta 60 segundos en despertar: espera un momento y vuelve a presionar **Calcular riesgo**. "
                       "Revisa también que la URL de la barra lateral sea correcta.")
            st.stop()
    if r.status_code == 422:
        detalle = r.json().get("detail", [])
        campos = ", ".join(str(d.get("loc", ["", "?"])[-1]) for d in detalle) or "desconocido"
        st.error(f"La API rechazó los datos (código 422). Revisa estos campos: {campos}. "
                 "Precio y flete no pueden ser negativos y n_items / n_vendedores deben ser al menos 1.")
        st.stop()
    if r.status_code != 200:
        st.error(f"La API respondió con el código {r.status_code}. Inténtalo de nuevo en unos segundos.")
        st.stop()
    res = r.json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Probabilidad de 1-2 estrellas", f"{res['probabilidad']:.1%}")
    c2.metric("Umbral del 10% más riesgoso", f"{res['umbral']:.1%}")
    c3.metric("¿Llamar al cliente?", "Sí" if res["riesgo_alto"] else "No")
    if res["riesgo_alto"]:
        st.error(f"🚨 Riesgo ALTO: {res['recomendacion']}.")
    else:
        st.success(f"✅ Riesgo normal: {res['recomendacion']}.")
    with st.expander("Respuesta JSON de la API"):
        st.json(res)
    with st.expander("Datos enviados"):
        st.code(json.dumps(valores, indent=2, ensure_ascii=False), language="json")
