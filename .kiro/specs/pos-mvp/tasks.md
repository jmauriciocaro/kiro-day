# Plan de implementación — MVP del POS

Tareas incrementales para construir el MVP. Cada tarea es un paso de código
ejecutable, se apoya en la anterior y referencia los requisitos que cubre.
Orden pensado para validar la lógica de negocio antes que la infraestructura.

- [x] 1. Preparar el esqueleto del backend
  - Crear `backend/` con `app/`, `tests/`, `requirements.txt` (fastapi, mangum, boto3, pydantic, pyjwt, passlib[bcrypt], pytest, moto).
  - `app/config.py`: leer de entorno tabla DynamoDB, región y nombre del parámetro SSM del secreto JWT (sin valores hardcodeados).
  - `app/main.py`: app FastAPI mínima con `GET /health` y handler Lambda vía Mangum.
  - _Requisitos: 6.2, 6.4_

- [x] 2. Definir los modelos de dominio (Pydantic)
  - `app/models.py`: `Product`, `SaleItemIn`, `SaleIn`, `SaleItem`, `Sale`, `DailyReport` con sus validaciones (precio > 0, stock >= 0, items no vacío, qty > 0, `payment_method` en {efectivo, tarjeta}).
  - Tests unitarios de validación de modelos (cantidades y precios inválidos se rechazan).
  - _Requisitos: 1.3, 2.5, 2.6_

- [x] 3. Implementar la capa de pago simulada
  - `app/payments.py`: `PaymentProvider` (Protocol) + `SimulatedPaymentProvider.charge()` que aprueba sin cobrar y devuelve una referencia `SIM-...`.
  - Test unitario del proveedor simulado.
  - _Requisitos: 2.7_

- [x] 4. Capa de acceso a datos (repositorio DynamoDB)
  - `app/repository.py`: `get_product(sku)`, `list_products()`, `create_product()` con `attribute_not_exists(PK)` para SKU único, `update_product()`.
  - Mapear entidades a `PK`/`SK` según el diseño de tabla única.
  - Tests de integración con `moto`: crear/listar/obtener/actualizar y rechazo de SKU duplicado.
  - _Requisitos: 1.1, 1.2, 1.4, 1.5, 1.6, 6.3_

- [x] 5. Lógica de negocio de ventas (cálculo + validación)
  - `app/services.py`: construir la venta a partir de `SaleIn` — resolver SKUs, calcular `total` en el servidor desde el precio actual, validar existencia y stock suficiente, armar `items[]` desnormalizado.
  - Tests unitarios: total correcto, SKU inexistente rechazado, stock insuficiente rechazado, venta vacía rechazada.
  - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Registro de venta atómico (TransactWriteItems)
  - `app/repository.py`: `register_sale()` con `TransactWriteItems` = `Put(SALE)` + por ítem `Update(stock -= qty)` con `ConditionExpression stock >= qty`.
  - Mapear `TransactionCanceledException` a error de "sin stock / intente de nuevo".
  - Tests de integración (moto): descuento correcto; venta cancelada no crea nada ni descuenta; caso de carrera (una venta gana, la otra recibe 409).
  - _Requisitos: 3.1, 3.2, 3.3_

- [x] 7. Reporte de ventas del día
  - `app/repository.py`: `list_sales_by_day(date)` con `Query(PK=SALE#yyyy-mm-dd)` ordenado por `SK`.
  - `app/services.py`: `daily_report(date?)` que calcula total y conteo; fecha por defecto = hoy UTC; lista vacía con total 0 si no hay ventas.
  - Tests: ventas ordenadas por hora, total/conteo correctos, día sin ventas devuelve lista vacía (no error).
  - _Requisitos: 4.1, 4.2, 4.3, 4.4_

- [x] 8. Autenticación y roles
  - `app/auth.py`: `POST /auth/login` (verifica `passwordHash` con bcrypt, firma JWT `{sub, role, exp}`); dependencia `require_role(*roles)` que valida el JWT y el rol.
  - Semilla de usuarios (cajero/dueño) leída de configuración, no del repo.
  - Tests: login ok/fallido, token inválido rechazado, `require_role` permite/deniega según rol.
  - _Requisitos: 7.1, 7.2, 7.3, 7.5, 7.6_

- [x] 9. Exponer la API (rutas FastAPI)
  - `app/main.py`: cablear rutas `GET/POST /products`, `GET /products/{sku}`, `PATCH /products/{sku}`, `POST /sales`, `GET /reports/daily`, aplicando `require_role` (reporte y alta/edición de producto solo `dueno`; resto cajero/dueño).
  - Manejadores de error que devuelven mensajes en español con los códigos HTTP del diseño.
  - Tests de API con `TestClient`: códigos y mensajes por caso (409 SKU duplicado, 404 no encontrado, 409 sin stock, 401/403 auth).
  - _Requisitos: 1._, 2._, 3._, 4._, 5.4, 7.4_

- [x] 10. Infraestructura como código (AWS SAM)
  - `backend/template.yaml`: función Lambda (FastAPI vía Mangum), HTTP API y tabla `pos` (PK/SK, on-demand); secreto JWT por parámetro/SSM, nunca en el repo.
  - Verificar `sam build` y `sam local start-api` contra la tabla local.
  - _Requisitos: 6.2, 6.3, 6.4_

- [x] 11. Esqueleto del frontend (React + Vite + TS)
  - `frontend/` con Vite + TS; `src/types.ts` espejo de los modelos; `src/api/client.ts` con `VITE_API_URL` por entorno e inyección de `Authorization`.
  - Pantalla de **Login** que obtiene y guarda el JWT.
  - _Requisitos: 5._, 7.1_

- [x] 12. Pantalla de Caja (cajero)
  - `components/Catalogo`, `components/Carrito`, `components/Recibo` y `pages/Caja`: listar catálogo (nombre/precio/stock), agregar al carrito con cantidades y total, confirmar con método de pago, mostrar recibo en pantalla.
  - Mostrar el mensaje de error del backend (ya en español) cuando la venta se rechaza.
  - _Requisitos: 5.1, 5.2, 5.3, 5.4_

- [x] 13. Pantalla de Reporte (dueño)
  - `pages/Reporte`: selector de fecha (hoy por defecto), lista de ventas del día con total y conteo; restringida al rol `dueno`.
  - _Requisitos: 4._, 5.5, 7.4_

- [x] 14. Integración end-to-end y verificación final
  - Levantar backend (`sam local` o `uvicorn`) + frontend (`npm run dev`) y validar el flujo completo: login → venta → stock descontado → reporte del día.
  - Correr toda la suite de tests del backend y asegurar que el hook `qa-tests` pasa en verde.
  - Checklist de despliegue: `VITE_API_URL`, secreto JWT en SSM, sin secretos en el repo.
  - _Requisitos: 6.1, 6.2, 6.4_
