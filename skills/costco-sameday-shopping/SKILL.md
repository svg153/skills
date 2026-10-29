---
name: costco-sameday-shopping
description: "Trigger: Costco España, Costco Same-Day, Instacart Costco, ofertas Costco Getafe, cesta Costco, reparto o recogida. Investiga catálogo y compara costes reales."
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Costco Same-Day Shopping

## Activation Contract

Usa esta skill al investigar productos, descuentos y pedidos de Costco España, especialmente al comparar entrega Same-Day, Uber Eats y visita al almacén.

## Hard Rules

- Prioriza `https://sameday.costco.es/` y `https://www.costco.es/catalogo-precios-promos`; Uber Eats es un contraste, no la fuente canónica de precios Costco.
- Distingue precios observados de precios confirmados hoy. Las páginas indexadas pueden mostrar ofertas caducadas: verifica fecha de fin en cada ficha y fecha de consulta.
- No afirmes stock ni entrega en una dirección sin comprobar catálogo del almacén y código postal en una sesión válida. Nunca solicites ni publiques credenciales, número de socio, dirección completa ni datos de pago.
- Identifica artículo, SKU, marca, variedad y formato. Separa unidades de compra de unidades interiores del pack; no sustituyas productos preparados sin confirmar ingredientes.
- No eludas autenticación, protecciones técnicas ni condiciones de uso. No hagas pedidos ni finalices pagos sin instrucción explícita.

## Decision Gates

| Situación | Acción |
| --- | --- |
| Catálogo público visible | Extraer ficha, precio, formato, SKU, enlace y evidencia temporal |
| Oferta anunciada | Contrastar vigencia en ficha y folleto oficial; si expirada, descartar |
| Página requiere sesión/dirección | Marcar disponibilidad, tarifa y stock como pendientes; pedir solo la comprobación necesaria |
| Diferencia Same-Day vs Uber Eats | Comparar mismo SKU y presentación, cesta y cargos finales |
| Pedido frente a visita | Comparar entrega total con desplazamiento incremental, tiempo y transporte de frío |

## Execution Steps

1. Identifica almacén (Getafe o Las Rozas), fecha, lista de compra y cantidades ambiguas.
2. Busca por nombre, variantes ortográficas, marca y SKU en fichas Same-Day; consulta `references/sources.md` para rutas verificadas.
3. Consulta el folleto oficial vigente, abre las fichas candidatas y verifica descuentos y fecha final. No promociones basadas solo en resultados almacenados.
4. Calcula unidades y precio por kg/unidad, subtotal y mínimo vigente (referencia histórica: 35 EUR; reconfirmar).
5. Comprueba tarifa de servicio y cobertura para el código postal antes de recomendar pedir; si no puedes, muestra expresamente la incógnita.
6. Compara Same-Day, Uber Eats y compra presencial con precios y gastos de cada canal. Penaliza productos extra añadidos solo para alcanzar un mínimo si no son necesarios.

## Output Contract

Entrega tabla con producto exacto, formato, cantidad, precio, fecha de verificación, estado de oferta/stock, fuente y link. Resume cesta, mínimos y costes confirmados frente a pendientes. Recomienda pedir o ir con sensibilidad por tarifa de entrega y tiempo de viaje, sin fingir certeza.

## References

- [Fuentes, búsquedas y productos de ejemplo](references/sources.md).
