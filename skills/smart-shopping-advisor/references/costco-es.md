# Costco España profile

Store profile for `smart-shopping-advisor`. It records stable structure only; verify every price, offer, fee, minimum, and stock status live and record the retrieval date. The user chooses the warehouse for each conversation.

## Scope

- Channels: warehouse visit, Costco Same-Day delivery (Costco-branded storefront operated on Instacart Storefront Pro, launched in Spain in 2026), and third-party delivery apps that may list Costco warehouses.
- Same-Day prices are based on warehouse prices but the site warns they can differ slightly; delivery-app prices are a separate channel.

## Official sources

| Purpose | URL |
| --- | --- |
| Same-Day home | https://sameday.costco.es/ |
| Same-Day public storefront | https://sameday.costco.es/store/costco-espana/storefront |
| Same-Day help: minimum order, fees, coverage | https://sameday.costco.es/store/costco-espana/pages/help |
| Same-Day terms: substitutions, payment | https://sameday.costco.es/store/costco-espana/pages/terms-conditions |
| Current offers flyer (Costco España) | https://www.costco.es/catalogo-precios-promos |
| Launch announcement (context only) | https://company.instacart.com/pressreleases/costco-launches-first-same-day-websites-in-france-and-spain-with-instacart |

Third-party delivery listings are a contrast channel, never the canonical source for Costco prices.

## Access gates

- Product pages under `/store/costco-espana/products/<id>-<slug>` are often publicly indexed and identify the item, brand, and pack format.
- Warehouse assignment, stock, delivery coverage, exact service fee, and checkout totals depend on a session and postcode. Mark them pending when they cannot be checked; ask the user only for the check that is needed (for example, "confirm the service fee shown at checkout"), never for credentials, membership number, full address, or payment data.
- Do not bypass login, bot protection, or terms of use; do not place orders without an explicit request.

## Fees, minimum, and membership

- Same-Day publishes a minimum order and a service fee on the help page; both can change, so read them on each comparison and cite the retrieval date.
- Warehouse purchases require Costco membership; check the current membership types and fees on costco.es if the user is not already a member, and apply the membership amortization model in `channel-profiles.md`.

## Offers

- Product pages and the flyer show discount windows ("Válido del ... al ...", "Termina el ..."). An offer counts only when the window covers the planned purchase date.
- Search-engine snapshots of product pages can show expired discounts or old stock states; treat them as catalog evidence only.

## Product identity

- Identify item number or product id, brand (Kirkland Signature is the private label), variety, and format.
- Many items are multipacks (for example, `4 x 660 g`): compute per-unit price from inner units and keep the purchase unit for quantities.
- Prepared foods and trays: do not assume fillings or ingredients from the title; check the product page or label and mention allergen uncertainty.

## Search tips when the storefront is gated

- `site:sameday.costco.es/store/costco-espana/products "<brand or product>"`
- `site:sameday.costco.es/store/costco-espana/products "Termina el" "descuento"`
- `site:costco.es/catalogo-precios-promos "Válido del"`
- Try spelling variants without accents; product slugs often drop accented characters.

## Known pitfalls

- Same-Day, delivery-app, and warehouse prices can differ for the same SKU; compare identical SKU and format.
- Substitutions may be applied to out-of-stock items; for perishables and prepared foods, state the substitution preference.
- Large formats can be poor value when the household will not consume them before expiry.
- For warehouse visits, include incremental travel and cold-chain transport for chilled or frozen items.
