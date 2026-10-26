import streamlit as st

st.set_page_config(page_title="Olist · del pedido a la reseña", page_icon="📦", layout="wide")

paginas = [
    st.Page("paginas/riesgo.py", title="Riesgo de un pedido", icon=":material/warning:", default=True),
    st.Page("paginas/comentarios.py", title="Comentarios (Deep Learning)", icon=":material/chat:"),
    st.Page("paginas/pronostico.py", title="Pronóstico Junio 2018", icon=":material/trending_up:"),
    st.Page("paginas/ficha.py", title="Ficha del Modelo", icon=":material/description:"),
]
st.navigation(paginas).run()
