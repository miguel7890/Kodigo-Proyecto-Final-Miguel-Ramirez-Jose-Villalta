"""API de riesgo de mala reseña (Olist)."""
import json
import os
from typing import Optional

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

import preparacion  # noqa: F401  (necesario para deserializar el pipeline)

BASE = os.path.dirname(os.path.abspath(__file__))
ENTRADAS = [
    "order_id", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date", "estado_cliente", "n_items",
    "n_vendedores", "precio_total", "flete_total", "peso_total_g", "fotos_promedio", "categoria",
    "estado_vendedor", "tipo_pago", "cuotas_max",
]

modelo = joblib.load(os.path.join(BASE, "modelo_riesgo.joblib"))
with open(os.path.join(BASE, "umbral_riesgo.json")) as f:
    UMBRAL = float(json.load(f)["umbral_riesgo_alto"])

app = FastAPI(title="API de Riesgo Olist", description="Probabilidad de que un pedido entregado reciba 1-2 estrellas.")


class PedidoInput(BaseModel):
    order_id: str
    order_purchase_timestamp: str
    order_approved_at: Optional[str] = None
    order_delivered_carrier_date: Optional[str] = None
    order_delivered_customer_date: str
    order_estimated_delivery_date: str
    estado_cliente: str
    n_items: int = Field(..., ge=1)
    n_vendedores: int = Field(..., ge=1)
    precio_total: float = Field(..., ge=0)
    flete_total: float = Field(..., ge=0)
    peso_total_g: Optional[float] = Field(None, ge=0)
    fotos_promedio: Optional[float] = Field(None, ge=0)
    categoria: Optional[str] = None
    estado_vendedor: str
    tipo_pago: Optional[str] = None
    cuotas_max: Optional[int] = Field(1, ge=0)


@app.get("/")
def raiz():
    return {"status": "ok", "servicio": "API de Riesgo Olist", "modelo_cargado": modelo is not None,
            "umbral_riesgo_alto": UMBRAL}


@app.post("/riesgo")
def riesgo(pedido: PedidoInput):
    fila = pd.DataFrame([pedido.model_dump()])[ENTRADAS]
    prob = float(modelo.predict_proba(fila)[:, 1][0])
    alto = prob >= UMBRAL
    return {
        "order_id": pedido.order_id,
        "probabilidad": round(prob, 4),
        "riesgo_alto": bool(alto),
        "umbral": round(UMBRAL, 4),
        "recomendacion": "Contactar al cliente inmediatamente" if alto else "No requiere llamada prioritaria",
    }
