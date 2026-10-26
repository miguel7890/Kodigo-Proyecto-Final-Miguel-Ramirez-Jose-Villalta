import pandas as pd
import plotly.express as px
import streamlit as st

from utils import leer_csv

st.title("Comentarios: sentimiento del texto vs estrellas")
st.caption("Muestra aleatoria de comentarios clasificada con cardiffnlp/twitter-xlm-roberta-base-sentiment.")
df = leer_csv("sentimiento_muestra.csv")
orden = ["negative", "neutral", "positive"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Comentarios analizados", f"{len(df):,}")
c2.metric("Coincidencia global", f"{df['coincide'].mean():.1%}")
c3.metric("Desacuerdos", f"{(~df['coincide']).sum():,}")
por_cat = df.groupby("sentimiento_estrellas")["coincide"].mean().reindex(orden)
c4.metric("Coincidencia en 1-2 estrellas", f"{por_cat['negative']:.1%}")

st.subheader("Tabla cruzada: estrellas vs RoBERTa")
modo = st.radio("Mostrar", ["Conteos", "% por fila"], horizontal=True)
tabla = pd.crosstab(df["sentimiento_estrellas"], df["sentimiento_modelo"],
                    normalize="index" if modo != "Conteos" else False).reindex(index=orden, columns=orden, fill_value=0)
if modo != "Conteos":
    tabla = (tabla * 100).round(1)
fig = px.imshow(tabla, text_auto=True, color_continuous_scale="Blues",
                labels=dict(x="Sentimiento del texto (RoBERTa)", y="Sentimiento de las estrellas", color=modo))
st.plotly_chart(fig, width="stretch")
st.dataframe(por_cat.mul(100).round(1).rename("% coincidencia").to_frame(), width="content")

st.subheader("Explorador de desacuerdos")
des = df[~df["coincide"]].copy()
tipos = st.multiselect("Tipo de desacuerdo", sorted(des["tipo_desacuerdo"].unique()), default=sorted(des["tipo_desacuerdo"].unique()))
solo_analizados = st.toggle("Solo los analizados manualmente (con veredicto)", value=False)
des = des[des["tipo_desacuerdo"].isin(tipos)]
if solo_analizados:
    des = des[des["quien_se_equivoco"].fillna("") != ""]
st.caption(f"{len(des)} comentarios")
cols = ["review_score", "sentimiento_estrellas", "sentimiento_modelo", "confianza_modelo",
        "review_comment_message", "traduccion", "quien_se_equivoco", "explicacion"]
st.dataframe(des[cols].fillna(""), width="stretch", hide_index=True)
