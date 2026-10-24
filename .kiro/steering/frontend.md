---
inclusion: fileMatch
fileMatchPattern: "**/*.{tsx,jsx,css}"
---

# Reglas de Frontend (reporth)

- Componentes funcionales con hooks; nada de componentes de clase.
- La UI debe ser clara para personal administrativo de una organización
  (p. ej. secretaría de un jardín): textos en español, flujos simples,
  confirmaciones antes de acciones irreversibles (quitar un reporte).
- Privacidad en la UI: nunca mostrar datos de otras organizaciones. En la
  consulta, mostrar solo el veredicto y el mínimo necesario para aceptar/denegar.
- Manejo cuidadoso de datos sensibles (cédula, registro civil): no cachearlos en
  el navegador más de lo necesario, no exponerlos en la URL.
- Accesibilidad: roles ARIA y foco de teclado en los formularios de reporte y
  consulta.
- Estado centralizado (un solo lugar de verdad) para la sesión de la organización.
