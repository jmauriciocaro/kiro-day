# Requisitos — MVP del POS

## Introducción

Sistema de punto de venta (POS) simple para tiendas de barrio y cafeterías. El
MVP cubre el ciclo mínimo para operar una caja: tener un catálogo de productos,
registrar una venta con varios ítems descontando stock de forma atómica, y
consultar las ventas del día. Está pensado para ser operado por personas sin
conocimientos técnicos, con el español como idioma del producto.

Alcance del MVP (según el steering de producto):
1. Catálogo de productos (nombre, precio, SKU, stock).
2. Registrar una venta (varios ítems, total, método de pago).
3. Descontar stock al vender.
4. Reporte de ventas del día.

La autenticación es **sencilla** (login básico con dos roles: cajero y dueño),
sin federación ni OAuth. El cobro del método de pago es **simulado** en el MVP:
se registra el método elegido pero no se procesa un cobro real; queda un punto
de integración claro para conectar una pasarela de pago más adelante.

Fuera de alcance del MVP: gestión de proveedores, devoluciones,
descuentos/promociones, multi-tienda, impresión física de recibos (se muestra en
pantalla) y cobro real con pasarela de pago.

## Requisitos

### Requisito 1 — Catálogo de productos

**Historia:** Como dueño/a de la tienda, quiero gestionar el catálogo de
productos, para que el cajero pueda venderlos y se controle el stock.

#### Criterios de aceptación

1. CUANDO el dueño crea un producto con nombre, precio, SKU y stock ENTONCES el
   sistema DEBERÁ guardarlo y devolver el producto creado.
2. CUANDO se intenta crear un producto con un SKU que ya existe ENTONCES el
   sistema DEBERÁ rechazar la operación con un error claro (SKU duplicado).
3. CUANDO se crea un producto con precio negativo o stock negativo ENTONCES el
   sistema DEBERÁ rechazar la operación con un error de validación.
4. CUANDO el cajero o el dueño solicita el catálogo ENTONCES el sistema DEBERÁ
   devolver la lista de todos los productos con su stock actual.
5. CUANDO se solicita un producto por su SKU ENTONCES el sistema DEBERÁ
   devolverlo, o un error "no encontrado" si no existe.
6. CUANDO el dueño actualiza el precio o el stock de un producto existente
   ENTONCES el sistema DEBERÁ persistir el cambio.

### Requisito 2 — Registrar una venta

**Historia:** Como cajero/a, quiero registrar una venta con varios productos,
para cobrar al cliente y dejar constancia de la transacción.

#### Criterios de aceptación

1. CUANDO el cajero registra una venta con una lista de ítems (SKU + cantidad) y
   un método de pago ENTONCES el sistema DEBERÁ calcular el total en el servidor
   a partir del precio actual de cada producto.
2. CUANDO la venta se registra correctamente ENTONCES el sistema DEBERÁ
   devolver la venta con su identificador, fecha/hora, ítems, total y método de
   pago.
3. CUANDO un ítem referencia un SKU inexistente ENTONCES el sistema DEBERÁ
   rechazar toda la venta con un error claro.
4. CUANDO la cantidad solicitada de un ítem supera el stock disponible ENTONCES
   el sistema DEBERÁ rechazar toda la venta indicando el producto sin stock
   suficiente.
5. CUANDO la venta no contiene ítems o una cantidad es menor o igual a cero
   ENTONCES el sistema DEBERÁ rechazar la operación con un error de validación.
6. El método de pago DEBERÁ ser uno de un conjunto permitido (efectivo,
   tarjeta).
7. El cobro del método de pago DEBERÁ ser SIMULADO en el MVP: el sistema
   registra el método y marca el pago como aprobado sin procesar un cobro real,
   a través de una capa aislada (interfaz de pago) que pueda reemplazarse luego
   por una pasarela real sin cambiar la lógica de la venta.

### Requisito 3 — Descontar stock al vender (atómico)

**Historia:** Como dueño/a, quiero que el stock se descuente automáticamente al
vender, para que el inventario siempre refleje la realidad.

#### Criterios de aceptación

1. CUANDO una venta se registra correctamente ENTONCES el sistema DEBERÁ
   descontar la cantidad vendida del stock de cada producto en la MISMA
   operación atómica que crea la venta.
2. SI el stock de cualquier ítem es insuficiente al momento de confirmar
   ENTONCES el sistema DEBERÁ no crear la venta y no descontar stock de ningún
   producto (todo o nada).
3. CUANDO dos ventas concurrentes intentan agotar el mismo producto ENTONCES el
   sistema DEBERÁ garantizar que el stock nunca quede negativo.

### Requisito 4 — Reporte de ventas del día

**Historia:** Como dueño/a, quiero ver las ventas de un día, para conocer cuánto
se vendió y conciliar la caja.

#### Criterios de aceptación

1. CUANDO el dueño solicita el reporte de un día (fecha) ENTONCES el sistema
   DEBERÁ devolver todas las ventas de ese día ordenadas por hora.
2. CUANDO se solicita el reporte ENTONCES el sistema DEBERÁ incluir el total
   acumulado del día y el número de ventas.
3. CUANDO no hay ventas en el día solicitado ENTONCES el sistema DEBERÁ devolver
   una lista vacía con total cero (no un error).
4. SI no se indica fecha ENTONCES el sistema DEBERÁ usar el día actual (UTC).

### Requisito 5 — Interfaz de caja (frontend)

**Historia:** Como cajero/a sin conocimientos técnicos, quiero una pantalla
simple, para registrar ventas y ver el catálogo sin confundirme.

#### Criterios de aceptación

1. CUANDO el cajero abre la aplicación ENTONCES el sistema DEBERÁ mostrar el
   catálogo de productos con nombre, precio y stock.
2. CUANDO el cajero agrega productos a una venta ENTONCES la interfaz DEBERÁ
   mostrar el carrito con cantidades y el total calculado.
3. CUANDO el cajero confirma la venta y elige método de pago ENTONCES la
   interfaz DEBERÁ enviar la venta al backend y mostrar una confirmación con el
   recibo en pantalla.
4. CUANDO el backend rechaza la venta (p. ej. sin stock) ENTONCES la interfaz
   DEBERÁ mostrar el mensaje de error en español de forma comprensible.
5. CUANDO el dueño abre el reporte del día ENTONCES la interfaz DEBERÁ mostrar la
   lista de ventas y el total del día.

### Requisito 6 — Calidad y despliegue

**Historia:** Como equipo, queremos que la lógica de negocio esté probada y el
sistema sea desplegable en AWS serverless, para operar con confianza.

#### Criterios de aceptación

1. La lógica de negocio (cálculo de total, validación de stock, descuento
   atómico) DEBERÁ tener tests automatizados.
2. El backend DEBERÁ exponer una API HTTP (FastAPI) desplegable en AWS Lambda +
   API Gateway.
3. Los datos DEBERÁN persistir en una única tabla de DynamoDB con diseño de
   tabla única.
4. No DEBERÁ haber secretos ni credenciales en el código ni en el repositorio.

### Requisito 7 — Autenticación sencilla y roles

**Historia:** Como dueño/a, quiero un login básico con roles, para que el cajero
opere la caja y solo el dueño vea los reportes, sin montar un sistema de
identidad complejo.

#### Criterios de aceptación

1. CUANDO una persona accede a la aplicación ENTONCES el sistema DEBERÁ pedir un
   inicio de sesión sencillo (usuario y clave) antes de operar.
2. El sistema DEBERÁ soportar dos roles: `cajero` y `dueño`.
3. CUANDO un usuario autenticado llama a la API ENTONCES el backend DEBERÁ
   validar la sesión/token antes de ejecutar la operación.
4. CUANDO un usuario con rol `cajero` intenta ver el reporte de ventas del día
   ENTONCES el sistema DEBERÁ permitir registrar ventas y ver el catálogo, pero
   el reporte DEBERÁ quedar restringido al rol `dueño`.
5. CUANDO las credenciales son inválidas ENTONCES el sistema DEBERÁ rechazar el
   acceso con un mensaje claro en español.
6. Las credenciales y secretos de sesión NO DEBERÁN estar escritos en el código
   ni en el repositorio (se leen de configuración/entorno).

> Nota: la autenticación del MVP es deliberadamente simple (login básico con
> roles). No incluye registro de usuarios self-service, recuperación de clave,
> OAuth ni federación; esos quedan para iteraciones posteriores.
