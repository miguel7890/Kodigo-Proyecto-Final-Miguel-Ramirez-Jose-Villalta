# Ficha del modelo · Riesgo de mala reseña (Olist)

**Equipo:** Ramirez Miguel y [Apellido2 Nombre2] · **Modelo:** XGBoost dentro de un pipeline de scikit-learn (`modelo_riesgo.joblib`) · **Umbral de alerta:** probabilidad ≥ 0.2678 (10% de pedidos más riesgosos)

## 1. Para qué sirve y para qué NO debe usarse

**Sirve para:** en el momento en que se confirma la entrega de un pedido, estimar la probabilidad de que el cliente deje una reseña de **1 o 2 estrellas**. Con esa probabilidad, el equipo de atención al cliente (que solo puede llamar al **10%** de los pedidos) prioriza las **llamadas preventivas** a los clientes con mayor riesgo, para resolver el problema antes de que escriban la reseña.

**NO debe usarse para:**
- Multar, bloquear o rankear vendedores de forma automática (el retraso muchas veces lo causa Correios o la transportadora, no el vendedor).
- Negar ventas, cambiar precios o tratar distinto a clientes según su estado o medio de pago.
- Predecir la reseña de pedidos cancelados o que aún no se han entregado (el modelo necesita la fecha real de entrega).
- Reemplazar la lectura de los comentarios: no sabe *por qué* el cliente está molesto.

## 2. Datos utilizados

- **Fuente:** base de datos PostgreSQL de Olist, esquema `final` (tablas `orders`, `customers`, `order_items`, `products`, `sellers`, `order_payments`, `order_reviews`).
- **Periodo:** pedidos comprados entre el **15-sep-2016** y el **31-may-2018**.
- **Población:** **77,304 pedidos** entregados (`delivered`), con fecha de entrega conocida y con reseña. El 13.54% (10,470) tiene 1-2 estrellas.
- **Qué se excluyó y por qué:** pedidos cancelados, no disponibles o en tránsito (no tienen entrega que evaluar); pedidos sin reseña (no sabemos si quedaron contentos); meses posteriores a mayo de 2018 (no están en la base). Tampoco se usa **nada de la reseña** (texto, largo del comentario, fechas de la reseña): esa información no existe cuando hay que decidir a quién llamar, y usarla inflaría falsamente los resultados.
- **Variables:** 17 datos del pedido (fechas de compra, aprobación, despacho, entrega y fecha prometida; estados del cliente y vendedor; artículos, vendedores, precio, flete, peso, fotos, categoría, medio de pago y cuotas) y 20 variables derivadas (días de retraso, si llegó tarde, tiempo de tránsito, flete/precio, etc.). Ver el diccionario en el notebook.

## 3. Qué tan bien funciona

Se probó como en la vida real: el modelo aprendió con el **80% más antiguo** de los pedidos (hasta el 22-mar-2018) y se evaluó con el **20% más reciente** (15,461 pedidos del 22-mar al 31-may-2018), que nunca vio. La medida es: *si llamamos al 10% de pedidos con más riesgo (1,546 llamadas), ¿qué porcentaje de esos clientes realmente iba a poner 1 o 2 estrellas?*

| Método | Aciertos en el 10% llamado |
|---|---|
| Llamar al azar | 11.9% |
| Llamar a los que llegaron con más días de retraso | 38.6% |
| Regresión logística | 46.6% |
| **Modelo (XGBoost)** | **48.8%** |

En palabras simples: **de cada 10 clientes que llamamos usando el modelo, unos 5 realmente iban a poner 1 o 2 estrellas**, frente a 1 de cada 10 llamando al azar y unos 4 mirando solo el retraso. El modelo es **4.1 veces mejor que el azar** y suma **10.3 puntos** sobre la regla del retraso.

## 4. Límites conocidos

- **Problemas que no dependen de la entrega:** producto defectuoso, equivocado o distinto a la foto que llegó a tiempo. El modelo no lo ve (el retraso es su señal principal: la variable `entrega_tardia` concentra ~70% de la importancia).
- **Periodos con muy pocos retrasos:** cuando casi todo llega a tiempo, el modelo pierde su mejor pista. En validación, mirando solo los pedidos que llegaron a tiempo, el acierto baja a **26.2%** (sigue siendo casi 3 veces el azar de 9.0%). En mayo de 2018 el acierto mensual fue 41.7% frente a 72.2% en marzo, que tuvo más retrasos.
- **Cambios en la logística:** huelgas (como la de camioneros de mayo de 2018), cambios de transportista o de la forma de calcular la fecha prometida cambian los patrones y pueden degradar el modelo.
- **Categorías o estados nuevos:** se tratan como "desconocido"; el modelo sigue funcionando pero con menos información.

## 5. A quién afecta un error

- **Falso positivo** (llamamos a un cliente que estaba contento): cuesta el tiempo de un agente y una llamada; el riesgo para el cliente es bajo (incluso puede valorar la atención).
- **Falso negativo** (no llamamos a un cliente que estaba molesto): el cliente deja 1-2 estrellas, baja la reputación del vendedor y de Olist, y quizá no vuelva a comprar. Con un cupo fijo del 10%, la mitad de los clientes molestos quedan fuera de la lista: el modelo ayuda, pero no los encuentra a todos.
- **Riesgos de mal uso:** castigar a vendedores por retrasos que causó la transportadora; usar el estado del cliente para darle peor servicio; confiar a ciegas en la probabilidad sin escuchar al cliente.

## 6. Recomendación de uso

1. **Flujo diario:** cada vez que se confirma una entrega, el sistema envía el pedido a la API (`POST /riesgo`). Si la probabilidad supera el umbral (0.2678), el pedido entra a la lista de llamadas del día, ordenada de mayor a menor riesgo.
2. **Supervisión humana:** el agente decide qué ofrecer (disculpa, cupón, cambio); el modelo solo prioriza. Ninguna sanción a vendedores se basa en el modelo.
3. **Monitoreo semanal:** porcentaje de llamados que terminan en 1-2 estrellas, tasa de entregas tardías y volumen de pedidos frente al pronóstico.
4. **Reentrenamiento mensual** con los pedidos más recientes, y antes si cambia la logística o si el acierto en el 10% cae por debajo de la regla del retraso (38.6%). Revisar el umbral si cambia la capacidad del equipo de llamadas.

## Uso de IA de Proyecto_Final.ipynb

Usamos un asistente de IA (Devin, de Cognition AI) como apoyo para: estructurar el código (consulta SQL con CTEs, `preparacion.py`, pipeline de scikit-learn, validación por fecha, pronóstico y clasificación de sentimiento), depurar errores de ejecución (p. ej. la serie con ceros en Holt-Winters) y diseñar la API en FastAPI y la app multipágina en Streamlit. También ayudó a redactar esta ficha y las respuestas del notebook.

Cómo validamos cada salida contra los datos reales:
- La consulta se verificó con la celda oficial de la plantilla (`Contrato completo: True | 77304 pedidos`).
- Todas las cifras de las respuestas y de esta ficha se copiaron de las salidas de las celdas ejecutadas del notebook (no hay cifras escritas a mano).
- Se comprobó que ninguna variable del modelo usa información de la reseña.
- La API se probó en local: `GET /` = 200, `POST /riesgo` con un pedido real = 200 con la misma probabilidad que el notebook, y `precio_total = -10` = 422.
- Las traducciones y la clasificación de los desacuerdos de sentimiento se revisaron leyendo cada comentario en portugués.

Todo lo entregado lo entendemos y lo podemos explicar en la defensa.
