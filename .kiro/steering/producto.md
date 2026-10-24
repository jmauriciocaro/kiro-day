---
inclusion: always
---

# Producto: reporth — central de reporte de deudas B2B

## El problema
En Colombia hay muchas empresas que prestan servicios por suscripción (jardines
infantiles privados, academias, gimnasios, servicios locales). No son lo
suficientemente grandes para pagar una suscripción a una central de riesgo, y
pierden mucho dinero: cuando un cliente no paga, simplemente cambia de
proveedor. Como los proveedores no se comunican entre sí, el siguiente les
presta el servicio sin saber que hay una deuda previa.

## Qué estamos construyendo
Una central de reporte de deudas **B2B** entre prestadores de servicios. Permite
reportar incumplimientos de pago y consultarlos antes de aceptar a un cliente
nuevo, llenando el vacío que dejan las centrales de riesgo tradicionales.

## Usuarios
- **Prestador de servicios (organización)**: el consumidor del sistema. Ejemplo:
  un jardín infantil privado. Reporta deudas, gestiona sus reportes y consulta
  antes de aceptar a un cliente.
- **Deudor reportado**: la persona (padre/acudiente) asociada a la deuda. No usa
  el sistema; recibe el cobro automático y puede ser dado de baja cuando paga.

## Funcionalidades núcleo (MVP)
1. **Reportar no pago / deuda** desde una organización: se registra el estudiante
   y se relaciona con el padre/acudiente responsable.
   - Estudiante: nombre + registro civil.
   - Padre/acudiente: nombre + cédula.
   - Más datos sensibles asociados a la deuda (monto, concepto, fechas).
2. **Consultar** a una persona antes de aceptarla, para decidir aceptar o denegar
   el servicio.
3. **Quitar reportes** (dar de baja una deuda, p. ej. cuando el deudor paga).
4. **Cobro automático por correo** a las personas adeudadas.

## Reglas de privacidad de datos (CRÍTICAS)
- Cada organización **solo puede ver los datos que ella misma aportó**.
- Al consultar a una persona, el que consulta solo ve lo necesario para **aceptar
  o denegar** — no el detalle completo de los reportes de otras organizaciones.
- Los datos son sensibles (cédula, registro civil de menores, deudas): se tratan
  con el máximo cuidado. Nada de exponerlos fuera de su organización dueña.

## Principios
- Demo **funcional y sencilla**: primero el MVP, sin sobre-ingeniería.
- No hay criterios de evaluación rígidos; el objetivo es que funcione y se
  entienda. El PRD aún NO está listo para esta sesión.
- Español como idioma del producto y de la comunicación del equipo.
