import plotly.graph_objects as go
import streamlit as st

from utils import leer_csv, leer_texto

st.title("Pronóstico de pedidos diarios · junio 2018")
pron = leer_csv("pronostico_junio.csv", parse_dates=["fecha"])
hist = leer_csv("serie_diaria.csv", parse_dates=["fecha"])
meta = leer_csv("metricas_pronostico.csv").set_index("metrica")["valor"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total junio pronosticado", f"{pron['pronostico'].sum():,.0f}")
c2.metric("Media diaria", f"{pron['pronostico'].mean():.1f}")
c3.metric("MAE validación (método elegido)", f"{meta['mae_modelo']:.1f}")
c4.metric("MAE ingenuo semanal", f"{meta['mae_ingenuo']:.1f}",
          delta=f"{meta['mae_modelo'] - meta['mae_ingenuo']:.1f}", delta_color="inverse")

desde = st.slider("Mostrar histórico desde", min_value=hist["fecha"].min().date(), max_value=hist["fecha"].max().date(),
                  value=hist["fecha"].max().date().replace(month=1, day=1))
h = hist[hist["fecha"].dt.date >= desde]
fig = go.Figure()
fig.add_trace(go.Scatter(x=h["fecha"], y=h["pedidos"], name="Histórico", line=dict(color="#555")))
fig.add_trace(go.Scatter(x=pron["fecha"], y=pron["alto"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=pron["fecha"], y=pron["bajo"], fill="tonexty", fillcolor="rgba(31,119,180,0.2)",
                         line=dict(width=0), name="Banda 80%"))
fig.add_trace(go.Scatter(x=pron["fecha"], y=pron["pronostico"], name="Pronóstico", line=dict(color="#1f77b4", width=3)))
fig.add_vrect(x0="2018-05-19", x1="2018-05-31", fillcolor="red", opacity=0.08, line_width=0,
              annotation_text="huelga", annotation_position="top left")
fig.update_layout(height=450, yaxis_title="pedidos por día", hovermode="x unified")
st.plotly_chart(fig, width="stretch")

st.subheader("Validación por fecha (MAE promedio, pedidos/día)")
st.dataframe(leer_csv("validacion_pronostico.csv"), width="content", hide_index=True)
st.subheader("Tabla del pronóstico")
st.dataframe(pron.assign(fecha=pron["fecha"].dt.strftime("%Y-%m-%d")), width="stretch", hide_index=True)
st.download_button("Descargar pronostico_junio.csv", leer_texto("pronostico_junio.csv"), "pronostico_junio.csv", "text/csv")
