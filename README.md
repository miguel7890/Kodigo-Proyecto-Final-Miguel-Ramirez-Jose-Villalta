# Proyecto Final Olist: Del Pedido a la Reseña

Proyecto final del Bootcamp de Machine Learning (Kodigo). A partir de los pedidos de Olist (e-commerce brasileño), el proyecto estima **qué entregas tienen más riesgo de recibir una reseña de 1 o 2 estrellas** para que el equipo de atención al cliente llame primero al 10% más riesgoso. Además pronostica los pedidos diarios de junio de 2018 y analiza el sentimiento de los comentarios con Deep Learning.

**Integrantes:** Ramirez Miguel y Jose Villalta

## Enlaces

| Servicio | URL |
|---|---|
| API de riesgo (FastAPI en Render) | https://kodigo-proyecto-final-miguel-ramirez.onrender.com |
| Documentación interactiva de la API | https://kodigo-proyecto-final-miguel-ramirez.onrender.com/docs |
| App (Streamlit Community Cloud) | https://kodigo-proyecto-final-miguel-ramirez-jose-villalta.streamlit.app/ |

> La API usa el plan gratuito de Render: si estuvo inactiva, la primera llamada puede tardar hasta ~60 segundos en responder.

## Resultados principales

| Componente | Resultado (validación por fecha) |
|---|---|
| Datos (Parte 1) | 77,304 pedidos entregados con reseña, 18 columnas del contrato |
| Modelo de riesgo (XGBoost) | `precision_en_10` = 0.4884 (azar 0.1189, regla del retraso 0.3855, regresión logística 0.4664) |
| Red neuronal Keras (extra) | `precision_en_10` = 0.4819 |
| Pronóstico junio 2018 | MAE 33.04 pedidos/día (ingenuo semanal 44.35); 6,779 pedidos en junio; banda 80% con cobertura 80.0% |
| Sentimiento (RoBERTa) | 68.8% de coincidencia con las estrellas en 1,200 comentarios |

## Arquitectura

```
PostgreSQL (Supabase, esquema final)
   │  SQL con CTEs: 1 fila por pedido (77,304 x 18)
   ▼
Proyecto_Final.ipynb ──► preparacion.py (crear_variables)
   │                        │
   │   Pipeline scikit-learn: FunctionTransformer(crear_variables)
   │   → ColumnTransformer (imputación + escalado + OneHotEncoder) → XGBClassifier
   │                        ▼
   │                 modelo_riesgo.joblib + umbral_riesgo.json
   │                        ▼
   │                 api/ (FastAPI en Render)  ◄── POST /riesgo ──  app/ (Streamlit)
   │
   ├─ Pronóstico de pedidos diarios (perfil semanal robusto) ─► pronostico_junio.csv ─► app/
   └─ Sentimiento con cardiffnlp/twitter-xlm-roberta-base-sentiment ─► sentimiento_muestra.csv ─► app/
```

- **SQL:** consulta con CTEs sobre `orders`, `customers`, `order_items`, `products`, `sellers`, `order_payments` y `order_reviews` (reseña más reciente con `DISTINCT ON`, pago principal por mayor `payment_value`, categoría y estado del vendedor del artículo 1).
- **Pipeline de scikit-learn con XGBoost:** `preparacion.py` crea 20 variables de negocio (días de retraso, entrega tardía, tiempos de despacho y tránsito, flete/precio, varios vendedores, etc.) sin usar ningún dato de la reseña. Validación temporal 80/20 y métrica `precision_en_10`.
- **FastAPI (`api/`):** carga el pipeline y el umbral al iniciar. `GET /` informa el estado y `POST /riesgo` valida los 17 campos con Pydantic (422 si hay precios negativos, `n_items < 1` o faltan campos) y devuelve probabilidad, `riesgo_alto` y recomendación.
- **Streamlit (`app/`):** app multipágina (`st.navigation`): *Riesgo de un pedido* (llama a la API), *Comentarios*, *Pronóstico Junio 2018* y *Ficha del Modelo*.
- **Deep Learning:** clasificación de sentimiento de comentarios en portugués con RoBERTa multilingüe (Hugging Face) y, como extra, una red densa en Keras comparada con XGBoost.

## Estructura del repositorio

```
Proyecto_Final.ipynb        notebook ejecutado con todas las salidas
preparacion.py              crear_variables(df) usada por el pipeline
modelo_riesgo.joblib        pipeline final entrenado con los 77,304 pedidos
pronostico_junio.csv        fecha, pronostico, bajo, alto (30 filas)
sentimiento_muestra.csv     muestra de 1,200 comentarios clasificados
ficha_modelo.md             ficha del modelo y declaración de uso de IA
api_url.txt / app_url.txt   URLs desplegadas
api/                        main.py, preparacion.py, modelo_riesgo.joblib, umbral_riesgo.json, requirements.txt
app/                        streamlit_app.py, paginas/, utils.py, requirements.txt y archivos de datos
```

## Ejecutar localmente

Requisitos: Python 3.12 (las versiones de `api/requirements.txt` son las mismas con las que se entrenó el modelo).

```bash
git clone https://github.com/miguel7890/Kodigo-Proyecto-Final-Miguel-Ramirez-Jose-Villalta.git
cd Kodigo-Proyecto-Final-Miguel-Ramirez-Jose-Villalta
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

**API (FastAPI):**

```bash
pip install -r api/requirements.txt
cd api
uvicorn main:app --reload --port 8000
# http://127.0.0.1:8000/  y  http://127.0.0.1:8000/docs
```

Ejemplo de llamada:

```bash
curl -X POST http://127.0.0.1:8000/riesgo -H "Content-Type: application/json" -d '{
  "order_id": "demo", "order_purchase_timestamp": "2018-05-01 10:00:00",
  "order_approved_at": "2018-05-01 10:30:00", "order_delivered_carrier_date": "2018-05-03 15:00:00",
  "order_delivered_customer_date": "2018-05-20 12:00:00", "order_estimated_delivery_date": "2018-05-15 00:00:00",
  "estado_cliente": "RJ", "n_items": 1, "n_vendedores": 1, "precio_total": 89.9, "flete_total": 18.5,
  "peso_total_g": 750, "fotos_promedio": 2, "categoria": "cama_mesa_banho", "estado_vendedor": "SP",
  "tipo_pago": "credit_card", "cuotas_max": 3}'
```

**App (Streamlit)**, en otra terminal:

```bash
pip install -r app/requirements.txt
cd app
streamlit run streamlit_app.py
```

Por defecto la app usa la API de Render. Para usar la API local, cambia la URL en la barra lateral a `http://127.0.0.1:8000` o crea `app/.streamlit/secrets.toml` con `API_URL = "http://127.0.0.1:8000"`.

**Notebook:** requiere además `jupyter`, `sqlalchemy`, `psycopg2-binary`, `statsmodels`, `matplotlib`, `transformers`, `torch` y `tensorflow`. La celda de conexión pide la contraseña del usuario de solo lectura del curso con `getpass`.

## Despliegue

- **Render (API):** Root Directory `api`, Build Command `pip install -r requirements.txt`, Start Command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Streamlit Community Cloud (app):** archivo principal `app/streamlit_app.py`; opcionalmente el secreto `API_URL`.
