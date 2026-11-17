# Store and channel profiles

A profile captures what is stable about a retailer or purchase channel so each comparison starts from verified structure instead of memory. Live prices, offers, fees, and stock always come from a fresh check.

## Profile template

Create `references/<store>-<country>.md` with these sections:

| Section | Content |
| --- | --- |
| Scope | Retailer, country, channels covered (warehouse/in-store, own delivery, third-party delivery app, pickup) |
| Official sources | Catalog, offers or flyer page, help/fees page, terms (substitutions, payment, returns) |
| Access gates | What needs a session, membership, store selection, or postcode; what is public |
| Fee structure | Which fees exist (delivery, service, small-basket, bag, tip) and where the current values are published; no amounts unless labelled with a retrieval date and "reconfirm" |
| Membership | Whether purchase requires membership, fee types, and where current fees are published |
| Offers | How validity windows are shown and how to tell expired indexed pages from current ones |
| Product identity | SKU format, pack/inner-unit conventions, private labels |
| Search tips | Public search patterns that find product pages when the storefront is gated |
| Known pitfalls | Channel price differences, substitutions, cached pages, regional assortment |

Do not record personal data: no home or work address, preferred warehouse, membership number, or order history. The user chooses the store or warehouse per conversation.

## Price evidence rules

- Record for each price: value, unit, format, channel, source URL, and retrieval date.
- An offer counts only if its validity window includes the purchase date. When the end date is not visible, mark it "validity unconfirmed".
- Indexed or cached pages are catalog evidence (the product exists, its format), not current price, stock, or offer evidence.
- Never derive one channel's price from another (for example, an in-store price from a delivery-app price).

## Per-unit normalization

`unit price = pack price / (number of inner units x size per unit)`; express in the most natural unit (EUR/kg, EUR/l, EUR/item). Compare per-unit prices only between equivalent products (brand tier, quality, preparation), and flag waste risk when a large pack exceeds what the household will consume before it spoils.

## Channel cost models

- Delivery: `sum(packs x verified channel price) + delivery fee + service fee + small-basket fee + other applicable charges - verified promotions`.
- Pickup: `sum(packs x verified channel price) + pickup fee + incremental travel`.
- In-store visit: `sum(packs x verified store price) + incremental travel (fuel/tolls/parking or fare) + optional time value`, reported separately from money.
- Minimum order: when a basket is below the minimum, report the shortfall and either the fee to proceed or the cost of necessary items that could be brought forward. Do not count unnecessary filler as savings.
- When a fee or price is pending (needs session or postcode), show the comparison as a range or a break-even fee ("delivery wins if total fees stay below X EUR").

## Membership amortization

Count a membership fee only when the user is not already a member or the decision is about renewing or upgrading.

- `annual fee / expected purchases per year = fee per purchase`.
- `break-even annual spend = annual fee / average saving rate versus the best alternative`.
- Include rewards or cashback only when the program terms are verified, and note that savings estimates depend on the basket mix.

## Output additions for baskets

Add per line: purchase format, quantity, per-unit price, offer end date or status, stock status, retrieval date. Summarize per channel: subtotal, confirmed fees, pending fees, minimum-order status, total, and the recommendation with its sensitivity to pending values.
