"""Variables de negocio para el modelo de riesgo de Olist.

Solo usa las 17 columnas de entrada del contrato (nada de la reseña), por lo que
puede calcularse en el momento en que se confirma la entrega.
"""
import numpy as np
import pandas as pd

COLUMNAS_FECHA = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
COLUMNAS_NUMERICAS_ORIGINALES = [
    "n_items", "n_vendedores", "precio_total", "flete_total",
    "peso_total_g", "fotos_promedio", "cuotas_max",
]
COLUMNAS_CATEGORICAS = ["estado_cliente", "estado_vendedor", "categoria", "tipo_pago"]
VARIABLES_NUEVAS = [
    "dias_retraso", "entrega_tardia", "dias_retraso_pos", "dias_adelanto",
    "dias_entrega_total", "dias_aprobacion", "dias_despacho_carrier", "dias_transito",
    "dias_estimados_total", "ratio_entrega_estimado", "retraso_carrier",
    "ratio_flete_precio", "valor_total_pedido", "precio_por_item", "flete_por_item",
    "peso_por_item", "multi_item", "multi_vendedor", "vendedores_por_item",
    "mismo_estado",
]
COLUMNAS_NUMERICAS = VARIABLES_NUEVAS + COLUMNAS_NUMERICAS_ORIGINALES


def _dias(fin, inicio):
    return (fin - inicio).dt.total_seconds() / 86400.0


def crear_variables(df):
    """Recibe las 17 columnas de entrada del contrato y devuelve variables numéricas y categóricas."""
    X = pd.DataFrame(df).copy()

    for col in COLUMNAS_FECHA:
        if col not in X:
            X[col] = pd.NaT
        X[col] = pd.to_datetime(X[col], errors="coerce")
    for col in COLUMNAS_NUMERICAS_ORIGINALES:
        if col not in X:
            X[col] = np.nan
        X[col] = pd.to_numeric(X[col], errors="coerce").astype(float)
    for col in COLUMNAS_CATEGORICAS:
        if col not in X:
            X[col] = np.nan
        X[col] = X[col].astype(object).where(X[col].notna(), np.nan)

    compra = X["order_purchase_timestamp"]
    aprobado = X["order_approved_at"]
    carrier = X["order_delivered_carrier_date"]
    entregado = X["order_delivered_customer_date"]
    estimado = X["order_estimated_delivery_date"]

    n_items = X["n_items"].fillna(1).clip(lower=1)

    X["dias_retraso"] = _dias(entregado, estimado)
    X["entrega_tardia"] = (X["dias_retraso"] > 0).astype(int)
    X["dias_retraso_pos"] = np.maximum(0, X["dias_retraso"])
    X["dias_adelanto"] = np.maximum(0, -X["dias_retraso"])
    X["dias_entrega_total"] = _dias(entregado, compra)
    X["dias_aprobacion"] = _dias(aprobado, compra)
    X["dias_despacho_carrier"] = _dias(carrier, aprobado)
    X["dias_transito"] = _dias(entregado, carrier)
    X["dias_estimados_total"] = _dias(estimado, compra)
    X["ratio_entrega_estimado"] = X["dias_entrega_total"] / np.maximum(1.0, X["dias_estimados_total"])
    X["retraso_carrier"] = (carrier > estimado).astype(int)
    X["ratio_flete_precio"] = X["flete_total"] / np.maximum(0.01, X["precio_total"])
    X["valor_total_pedido"] = X["precio_total"] + X["flete_total"]
    X["precio_por_item"] = X["precio_total"] / n_items
    X["flete_por_item"] = X["flete_total"] / n_items
    X["peso_por_item"] = X["peso_total_g"] / n_items
    X["multi_item"] = (X["n_items"] > 1).astype(int)
    X["multi_vendedor"] = (X["n_vendedores"] > 1).astype(int)
    X["vendedores_por_item"] = X["n_vendedores"] / n_items
    X["mismo_estado"] = (X["estado_cliente"] == X["estado_vendedor"]).astype(int)

    salida = X[COLUMNAS_NUMERICAS + COLUMNAS_CATEGORICAS].copy()
    salida[COLUMNAS_NUMERICAS] = salida[COLUMNAS_NUMERICAS].astype(float).replace([np.inf, -np.inf], np.nan)
    return salida
