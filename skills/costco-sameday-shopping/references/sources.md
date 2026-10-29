# Fuentes públicas y guía de verificación

## Fuente oficial principal

- Inicio: https://sameday.costco.es/
- Catálogo público indexable: https://sameday.costco.es/store/costco-espana/storefront
- Ayuda, mínimos y cargos: https://sameday.costco.es/store/costco-espana/pages/help
- Términos, sustituciones y pagos: https://sameday.costco.es/store/costco-espana/pages/terms-conditions
- Folleto Costco España, debe revisarse en cada compra: https://www.costco.es/catalogo-precios-promos
- Plataforma logística: Instacart Storefront Pro, lanzamiento en España 30/01/2026: https://company.instacart.com/pressreleases/costco-launches-first-same-day-websites-in-france-and-spain-with-instacart
- Contraste Getafe por intermediario: https://www.ubereats.com/es/store/costco-getafe/RUVw_P56VBK3YOMK1TlL7A

## Fichas de ejemplo para localizar los SKUs

Los enlaces identifican productos; los precios y estados no son constantes.

| Producto | Ficha | Formato visto en octubre de 2026 |
| --- | --- | --- |
| Bandeja surtida de sándwiches BSF | https://sameday.costco.es/store/costco-espana/products/100655286-bandeja-surtida-de-sndwiches | 18 unidades; una consulta indexada la mostraba sin stock, no estado actual |
| Kirkland Signature Empanada Gallega | https://sameday.costco.es/store/costco-espana/products/97442806-empanada-gallega | 1 empanada; el relleno no se verifica por el título |
| Monjardín Tomate Triturado Extra Ecológico | https://sameday.costco.es/store/costco-espana/products/88120855-tomate-triturado-extra-de-cultivo-ecolgico | 4 x 660 g por unidad de compra |
| BSF Bandeja surtido Wrap | https://sameday.costco.es/store/costco-espana/products/100655112-bandeja-surtido-wrap | 1,55 kg |
| Fratelli Beretta Mortadela de Bolonia IGP | https://sameday.costco.es/store/costco-espana/products/88698364-fratelli-beretta-mortadela-de-bolonia-igp | 2 x 250 g; oferta indexada hasta 22/11/2026 |

## Cómo buscar cuando la portada no se puede consultar

Usa búsquedas públicas y enlaces exactos:

- `site:sameday.costco.es/store/costco-espana/products "Monjardín"`
- `site:sameday.costco.es/store/costco-espana/products "bandeja surtida" "sandwich"`
- `site:sameday.costco.es/store/costco-espana/products "Termina el" "descuento"`
- `site:costco.es/catalogo-precios-promos "Válido del"`

Una página indexada hace semanas o meses es *evidencia de catálogo*, no precio/stock/descargo vigente. Revalidar fecha de campaña, configuración de tienda y cesta. Nunca derivar precio presencial del precio Uber Eats. El sitio oficial describe precios de almacén con posibles pequeñas diferencias por actualizaciones, una tarifa de servicio y mínimo histórico de 35 EUR. La tarifa exacta y la disponibilidad dependen de la sesión y cobertura.

## Modelo económico

- `SameDay = suma(packs x precio de ficha verificado) + servicio + otros cargos aplicables`
- `UberEats = suma(packs x precio Uber verificado) + entrega + servicio - promociones aplicables`
- `Presencial = suma(precios de almacén verificados) + transporte incremental + valor del tiempo (separado, opcional)`
- Señalar claramente precio desconocido en lugar de inventar. Comprobar sustituciones para productos preparados y perecederos.
