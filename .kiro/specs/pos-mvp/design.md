# Diseño — MVP del POS

## Visión general

El POS es una aplicación serverless en AWS. El frontend es una SPA React + Vite
+ TypeScript servida por Amplify Hosting; el backend es una API FastAPI (Python
3.12) empaquetada en AWS Lambda detrás de API Gateway (HTTP API); los datos
viven en una única tabla de DynamoDB (`pos`) con diseño de tabla única. El cobro
del método de pago se abstrae tras una interfaz (`PaymentProvider`) con una
implementación simulada, de modo que una pasarela real pueda conectarse después
sin tocar la lógica de venta.

Este diseño cubre los 7 requisitos del `requirements.md`: catálogo (R1), venta
(R2), descuento atómico de stock (R3), reporte del día (R4), interfaz de caja
(R5), calidad y despliegue (R6) y autenticación sencilla con roles (R7).

## Arquitectura

```
Cajero/Dueño (navegador)
   → React SPA (Amplify Hosting)
      → API Gateway (HTTP API, valida JWT)
         → Lambda (FastAPI + Mangum)
            → DynamoDB (tabla única 'pos')   [TransactWrite: venta + stock]
            → PaymentProvider (simulado)      [charge() sin cobro real]
```

Diagrama interactivo (draw.io):
<https://app.diagrams.net/?pv=0&grid=0#R7Vldc%2BI2FP01zLYPzdgYcPYRQ7K7neyUKZnNY%2BdiCaNGllxZDrC%2Fvle2DLblZNouIZMmCR%2F20ZV0de45BotBMEt3nxRkm6%2BSUD4YekAg0%2ByBziSXKh8E88FwCIWW%2BIatZFchl55ngX0FTGogUYxUkH8Eluw7tWAdVjBC81aglpJrlrXBWApBY93CQCm5bYetJW%2FPmkFCHWAZA2%2BiwdUgmCkpdXWU7maUGw7qFVS5Xj%2FSehhYUaH%2FSQfNNE5fdnoAXthMFr8tEfj6bYGvv%2BBzqv4qmMY1FwrM6Z1pXlL1QBWneV71z%2FW%2BXommO5w92uiUI%2BDj4VoKbRn3J%2FW57WDagbNE4HGMeVOFAA6tGXIztQ0pI8RERzZZbKa7Rxd9pBKlRGVKtdpjiO0wsgW3OrEUeVtG9KaCwonFNpQlGztoYDGwdU4OAx8JxgPLcT%2FfMeQbhgvsMj6DP6lCQXtmpKE3L6iQDq35PdWxydBDHmShORPoiVqMnqW1dEnZIcD%2Fa5NHlCggjB7bhBSGyzXjvC8810re004wwdQpsRPV5bmBFeULmTPNpCnTSmot0576aZn1lfkRiQw7EjFTQp5VC12znckjyjeQmcZ0l5irxQVs89FFkZfj8jIvqhhWyADlDCeQzmVbOv6lq50%2B6UxOIB1IM87We0c6v1NAWtCPi%2BlgPBM%2FTes477PMNRPJz08LKZNM6DKvcYQPzHRWPccYOjPIxXDcA%2FZhoQv6bhi%2B%2BX0zdME%2BLHRB3w0zZ3XWbbAPC8duxt3efk9vv9MbH%2F%2FSlx0DzufBaDRzDIgt6%2FLv1bhQ0VwWKqZfYpNPhKfVUTuqVvTz2fVwzX7Cr%2BGl69ca%2ByG%2FZizZOm6dLr4g8Ak03cK%2B9Ovn21vzOYsN70Z9LUa9Cv1xGL0do2bsj8RK9vnMOvJezqwc0hUBx603FWxseg25rsw7GEbm2zGIpEjfLftqLDsPfc97M5a1gn4%2Bt47Dl3MrISvHqvO9gFTOo9KsGlbc3KkWAiuE7x8ymX949%2Bpr8epoHmLDm%2FEqKaWLmj6fW4PJ%2BdyagXvTuoB9iqkvlHxgBBdqTMtMFdbw3XiUpQUHAq5llSwEKQtvmNlumKbLDGLTukVGO0Vsy4r6ZEzDPll9nIQBTJqy6mrgRHUIPnbqELp18OsNyVPvIFDfoZOShNaylkpvZCIF8Ksj2qSTCjI1%2B5zGWVzG97VeI4jvk7IwNaWErqHgZg%2FQHt30xyVlxaqsTCpPs4qZl24auFtpGlRCbWxjo8Stg6IczF5ya9gfInXoiNvc0S0Pe3m%2F3t2enPamMr1TlaF7kTxcPauLEkeXpVVBys33%2F1q31j5Wq271DfM5qhb8n6zQ2GpoEnq8qTkHoyPHB7cKRA6xvlN4lX4dHjit1Jt3lc3C2O%2Bv56jK%2BOS8tz4iX1D0j5Frv26cnlw8Pf4wV7Y1fqUMrv4G>

### Decisiones clave

- **FastAPI en Lambda vía adaptador ASGI** (Mangum). Un solo handler enruta
  todas las rutas; mantiene el código idéntico a un servidor local (desarrollo
  con `uvicorn`, producción en Lambda).
- **DynamoDB tabla única**: patrones de acceso conocidos y acotados (catálogo,
  producto por SKU, venta, ventas del día). Capacidad on-demand (pay-per-request)
  para no gestionar throughput en una tienda pequeña.
- **IaC**: AWS SAM para el backend (función + tabla + HTTP API en una plantilla).
  Es la ruta más corta para FastAPI-en-Lambda; se decide con el arquitecto si se
  migra a CDK más adelante.
- **Auth sencilla con JWT propio** (validado con el arquitecto): la API firma un
  JWT corto al hacer login (HS256, secreto en **SSM SecureString**, nunca en el
  repo); contraseñas con **bcrypt/argon2**. No se introduce Cognito en el MVP
  (el requisito pide auth sencilla sin OAuth/federación, y 2 roles no justifican
  un IdP). La verificación del token queda aislada en una dependencia de FastAPI
  (`require_role`), reemplazable por Cognito más adelante sin tocar las rutas.
- **Pago simulado tras interfaz**: `PaymentProvider.charge()` devuelve
  `aprobado` sin cobrar; una `StripePaymentProvider` (u otra) podrá sustituirla.

> **Validación del arquitecto (resumen):** se confirman JWT propio y SAM para el
> MVP. Se descarta **Amplify Gen 2 full-stack** porque empuja a AppSync/GraphQL y
> al modelo de datos de Amplify, incompatible con la decisión de FastAPI +
> DynamoDB tabla única propio; queda como alternativa futura. CDK se reserva para
> cuando la infra crezca más allá de una función + una tabla.

## Modelo de datos (DynamoDB tabla única `pos`)

Clave primaria genérica `PK` (hash) + `SK` (range). Tres tipos de ítem.

| Entidad  | PK                  | SK                        | Atributos                                                         |
|----------|---------------------|---------------------------|-------------------------------------------------------------------|
| Producto | `PRODUCT#<sku>`     | `PRODUCT#<sku>`           | `name`, `price` (number), `stock` (number), `type="PRODUCT"`      |
| Venta    | `SALE#<yyyy-mm-dd>` | `SALE#<ts>#<saleId>`      | `total` (number), `paymentMethod`, `paymentStatus`, `cashier`, `items[]`, `type="SALE"` |
| Usuario  | `USER#<username>`   | `USER#<username>`         | `passwordHash`, `role` (`cajero`\|`dueno`), `type="USER"`         |

`items[]` se desnormaliza dentro de la venta como lista de objetos
`{ sku, name, qty, unitPrice }` — así el recibo y el reporte no necesitan releer
productos.

Diagrama ER (draw.io):
<https://app.diagrams.net/?pv=0&grid=0#create=%7B%22type%22%3A%22mermaid%22%2C%22compressed%22%3Atrue%2C%22data%22%3A%22lVNtb4IwEP41RP3QxEiMnxVMtmxGI%2FMHnHDTKlDWHlv497tSgi8Rx0jpXdvnjuvzHEIIbzwnSSl6%2FtybjDfriGfB70olmCp2ErQTkDJsh2GVQ6bCBfsE%2BxTYlrmMrR0UygxGnE%2FUWVGHEg4aMvb51CbfrsNd8GEXs0W764YhLfODBb3VG5MW7JtzyesufPRPPJePd2d5me1Rs1NoGXceGlLxuSsrVQXe1XFVwSxs%2FWj%2BvuxHgEP6FT8iy0SS9CChiSFjaYAUXx8EtRciRZB2ZSygyjCnFdJRJS45fmJM8lt5s4BAn5DgSUVNfERApXHxUGi1h8T21NDIbPQkOgZzlFzk7XEqDbGRhFmT0psumMla8KAWdhJ8UcUz9yRtajWZ%2B2n45FMX5Rx5j2XbRcttP9kc0i8NalfRn6L1jyjAmB%2BlkxempwujVdrcJ4YTaqtWUmKuelHgSnlMwfXfG%2FAQQlk6Li3tO%2BBEc6NozGPptMa81YzVutWipbU7ocYDy67hFw%3D%3D%22%2C%22effect%22%3A%22pop%22%2C%22version%22%3A%2212%22%7D>

### Patrones de acceso → operaciones DynamoDB

| # | Patrón de acceso                    | Operación                                                              |
|---|-------------------------------------|------------------------------------------------------------------------|
| 1 | Producto por SKU                    | `GetItem(PK=PRODUCT#sku, SK=PRODUCT#sku)`                              |
| 2 | Listar catálogo                     | `Query` por GSI de tipo, o `Scan` filtrando `type=PRODUCT` (catálogo pequeño en MVP) |
| 3 | Crear producto (SKU único)          | `PutItem` con `ConditionExpression attribute_not_exists(PK)`          |
| 4 | Registrar venta + descontar stock   | `TransactWriteItems`: `Put(SALE)` + por ítem `Update(stock -= qty)` con `ConditionExpression stock >= qty` |
| 5 | Ventas del día                      | `Query(PK=SALE#yyyy-mm-dd)` ordenado por `SK` ascendente              |

> **R3 (atomicidad):** la condición `stock >= qty` en cada `Update` dentro del
> `TransactWriteItems` garantiza que, si cualquier ítem no tiene stock, **toda**
> la transacción se cancela (`TransactionCanceledException`) y no se crea la
> venta ni se descuenta nada. Esto también resuelve la carrera concurrente (R3.3):
> DynamoDB evalúa las condiciones de forma serializada.

> Nota sobre el catálogo (patrón 2): el MVP usa `Scan` con filtro por simplicidad
> (pocos productos). Si el catálogo crece, se añade un GSI `type` para `Query` por
> prefijo y evitar el antipatrón de `Scan`.

## Backend — API (FastAPI)

Base URL: `/` servida por API Gateway. Todas las rutas (salvo `/auth/login`)
requieren `Authorization: Bearer <jwt>`.

| Método | Ruta                   | Rol        | Descripción                                   |
|--------|------------------------|------------|-----------------------------------------------|
| POST   | `/auth/login`          | público    | Devuelve JWT (usuario + rol) si credenciales ok |
| GET    | `/products`            | cajero/dueño | Lista el catálogo                            |
| GET    | `/products/{sku}`      | cajero/dueño | Un producto por SKU                          |
| POST   | `/products`            | dueño      | Crea un producto                              |
| PATCH  | `/products/{sku}`      | dueño      | Actualiza precio y/o stock                    |
| POST   | `/sales`               | cajero/dueño | Registra una venta (descuenta stock)         |
| GET    | `/reports/daily`       | dueño      | Reporte del día (`?date=yyyy-mm-dd`, por defecto hoy UTC) |

### Modelos (Pydantic) — resumen

```python
class Product(BaseModel):
    sku: str
    name: str
    price: Decimal      # > 0
    stock: int          # >= 0

class SaleItemIn(BaseModel):
    sku: str
    qty: int            # > 0

class SaleIn(BaseModel):
    items: list[SaleItemIn]        # no vacío
    payment_method: Literal["efectivo", "tarjeta"]

class SaleItem(SaleItemIn):
    name: str
    unit_price: Decimal

class Sale(BaseModel):
    sale_id: str
    created_at: str                # ISO-8601 UTC
    items: list[SaleItem]
    total: Decimal
    payment_method: str
    payment_status: str            # "aprobado" (simulado)
    cashier: str

class DailyReport(BaseModel):
    date: str
    sales: list[Sale]
    total: Decimal
    count: int
```

### Capa de pago (simulada, reemplazable)

```python
class PaymentProvider(Protocol):
    def charge(self, amount: Decimal, method: str) -> PaymentResult: ...

class SimulatedPaymentProvider:
    """MVP: aprueba siempre sin cobrar. Punto de integración para pasarela real."""
    def charge(self, amount, method) -> PaymentResult:
        return PaymentResult(status="aprobado", reference=f"SIM-{uuid4().hex[:8]}")
```

La implementación se inyecta como dependencia; reemplazarla por una pasarela
real (p. ej. Stripe) no cambia el handler de `/sales`.

### Autenticación y roles

- `POST /auth/login` recibe `{username, password}`, busca `USER#<username>`,
  verifica con `passwordHash` (bcrypt/argon2) y firma un JWT `{sub, role, exp}`.
- Una dependencia `require_role(*roles)` de FastAPI valida el JWT y el rol. El
  reporte (`/reports/daily`) exige `dueno`; el resto acepta `cajero` o `dueno`.
- Secreto de firma y seed de usuarios se leen de entorno/SSM — nunca del repo
  (R7.6, R6.4).

### Manejo de errores (mensajes en español para R5.4)

| Caso                         | HTTP | Cuerpo                                                     |
|------------------------------|------|------------------------------------------------------------|
| SKU duplicado al crear       | 409  | `{"error": "Ya existe un producto con ese SKU"}`           |
| Producto no encontrado       | 404  | `{"error": "Producto no encontrado"}`                      |
| Venta vacía / cantidad ≤ 0   | 422  | validación Pydantic + mensaje claro                        |
| SKU inexistente en venta     | 400  | `{"error": "El producto <sku> no existe"}`                 |
| Stock insuficiente           | 409  | `{"error": "Sin stock suficiente para <name>"}`            |
| Carrera (tx cancelada)       | 409  | `{"error": "Stock agotado, intente de nuevo"}`             |
| Credenciales inválidas       | 401  | `{"error": "Usuario o clave incorrectos"}`                 |
| Rol no autorizado            | 403  | `{"error": "No tienes permiso para esta acción"}`          |

## Flujo de registro de venta (R2 + R3)

```
1. Cajero envía POST /sales (items, método, JWT)
2. API Gateway pasa el evento a Lambda (FastAPI)
3. FastAPI valida JWT y rol
4. BatchGet de productos por SKU
5. Validar stock y calcular total en el servidor
   - si SKU inválido o sin stock → 400/409 con mensaje en español
6. PaymentProvider.charge(total, método) → aprobado (simulado)
7. TransactWriteItems: crear SALE + descontar stock (condición stock>=qty)
   - si la condición falla (carrera) → 409 "intente de nuevo"
   - si ok → commit
8. Responder 201 con la venta + recibo
```

Diagrama de secuencia (draw.io):
<https://app.diagrams.net/?pv=0&grid=0#create=%7B%22type%22%3A%22mermaid%22%2C%22compressed%22%3Atrue%2C%22data%22%3A%22jVRdb9swDPw1AdwHA1m7lz26cZJtLVCjydpnRmJTdbKVSnKG%2FPuRkmwnToMW8Ick353II%2BU8zyfTwiuvcXJTTK6nC92%2BGXrndD%2FiVjlvwdJ4j40HemcSnWhpwiDwplaCRxLp4bwRf69ILw%2BqDt8JKLBUsLVQ0wphmNV607T1Bm2%2FtAPrlVA7aDzNZgxyPIA3tCyfPSIIf3UBv%2BzwRfWLp%2BDxHxwugIsOvADnIyG7h3oj4ZJ81TEqONSUeWXNXklkVzKn6ku0sqOVhwZqU94y3sNGs4074wbeLJ%2FczOlaxhJUD6t1%2BLBwoJEVMuWxpgEbU6M30lSwNXH%2B%2B3k9KC2TUhGV5vtUqJ%2FrdRUQHITQoEit4xSnnCfQSoaSkzI9D3Rbo8%2FgZYTfghevS%2BSEd9bIVnjjQn6ssLr70%2FPK%2FHSf6gid7SwKlRLqu%2BiT8AIuBShAi1aHZW88DNGC5shWCaoa175QhcgVjA6nIPnTnpVNz%2Bx2T9vP4vbfp7yK1ob8sOGHo4IfGYTasfhTOjBBFs5ko2oVVcUr2C1mMfRRla9G1GrkI5DtG5AmdSO5IM84o5qtLTSOztOzpb5KEVgM7q2K%2B3nfKHzUDWVx7HZGK5IsNE2%2FyNLluz%2BMd43ez47wL6BD92cCrEULY8bHndKFSxozoP%2BJRvkh77xWPzhGNUQarLWoqPzcAaciqW4Pd18KSpi6Vv5LcVxPv02GH2i0lvt9M242bIbEaPwf%22%2C%22effect%22%3A%22pop%22%2C%22version%22%3A%2212%22%7D>

## Frontend (React + Vite + TypeScript)

Pantallas mínimas para un operador sin perfil técnico (R5):

- **Login**: usuario + clave → guarda el JWT (memoria/`sessionStorage`).
- **Caja (cajero)**: catálogo (nombre, precio, stock) → agregar al carrito →
  carrito con cantidades y total → elegir método de pago → confirmar → recibo en
  pantalla. Los errores del backend se muestran tal cual (ya vienen en español).
- **Reporte (dueño)**: selector de fecha (por defecto hoy) → lista de ventas del
  día + total y conteo.

Capa de datos: un cliente HTTP (`fetch`/axios) con el `Authorization` inyectado;
tipos TypeScript espejo de los modelos Pydantic. El `baseURL` de la API se
configura por variable de entorno de Vite (`VITE_API_URL`), nunca hardcodeado.

## Estructura de carpetas propuesta

```
backend/
├── app/
│   ├── main.py            # FastAPI app + rutas + handler Lambda (Mangum)
│   ├── models.py          # modelos Pydantic
│   ├── repository.py      # acceso a DynamoDB (GetItem/Query/TransactWrite)
│   ├── services.py        # lógica de negocio (total, validación, venta)
│   ├── payments.py        # PaymentProvider + SimulatedPaymentProvider
│   ├── auth.py            # login, JWT, require_role
│   └── config.py          # lee entorno (tabla, secreto JWT, región)
├── tests/
│   ├── test_services.py   # cálculo de total, validación de stock
│   └── test_sales.py      # descuento atómico (con moto/dynalite local)
├── template.yaml          # AWS SAM: Lambda + HTTP API + tabla DynamoDB
└── requirements.txt
frontend/
├── src/
│   ├── api/client.ts
│   ├── pages/{Login,Caja,Reporte}.tsx
│   ├── components/{Catalogo,Carrito,Recibo}.tsx
│   └── types.ts
├── index.html
├── package.json
└── vite.config.ts
```

## Estrategia de pruebas (R6.1)

- **Unitarias (lógica de negocio)**: cálculo de total desde precios del
  servidor; validación de venta vacía, cantidades ≤ 0, SKU inexistente; mensajes
  de error. Sin tocar AWS.
- **Integración de repositorio**: `TransactWriteItems` con una tabla DynamoDB
  local (`moto` o DynamoDB Local) para verificar el descuento atómico y que la
  condición `stock >= qty` cancela la venta cuando falta stock.
- **Caso de carrera (R3.3)**: dos ventas que agotan el mismo producto; se espera
  que una tenga éxito y la otra reciba `TransactionCanceledException` → 409.
- Framework: `pytest`. El hook `qa-tests` (Acto 6) corre los tests al escribir
  código del backend.

## Despliegue (R6.2, R6.3)

- **Backend**: `sam build && sam deploy` crea la función Lambda (FastAPI vía
  Mangum), el HTTP API y la tabla `pos` (on-demand). El secreto JWT se pasa por
  parámetro/SSM, no por el repo.
- **Frontend**: Amplify Hosting conectado al repo; build `npm run build`, output
  `dist`; `VITE_API_URL` apunta al endpoint del HTTP API. (Ver skill
  `deploy-amplify`.)
- **Alternativa**: Amplify Gen 2 full-stack; se decide con el arquitecto. El MVP
  asume SAM para el backend por el encaje directo con FastAPI.

## Seguridad y secretos (R6.4, R7.6)

- Sin credenciales ni secreto JWT en el repo: todo por variables de entorno /
  SSM Parameter Store.
- El hook `guard-shell` (Acto 6) bloquea comandos de shell peligrosos durante el
  desarrollo; el agente `deploy-ops` (Acto 8) tiene denegado leer `.env`/`*.pem`
  y ejecutar borrados destructivos.
- La verificación del JWT y los roles se aplican en cada ruta protegida.
