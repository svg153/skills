---
name: smart-shopping-advisor
description: "Research and compare products, services, or shopping baskets before a purchase, especially home, household, groceries, technology, networking, appliances, and smart-home equipment. Use when the user asks what to buy, shares product links, compares models, shops, or delivery channels (store pickup, same-day delivery, Instacart-style storefronts, warehouse clubs such as Costco España / Costco Same-Day), asks whether an offer, membership, or upgrade is worthwhile, or wants prices, per-unit cost, compatibility, alternatives, and a critical recommendation."
license: MIT
---

# Smart Shopping Advisor

## Principles

- Start with the user's outcome, existing equipment, physical constraints, budget, location, and recurring costs; retrieve prior context only when it would materially change the decision.
- Challenge the premise when repairing, borrowing, delaying, buying used, changing configuration, or choosing a different product category would solve the problem better.
- Research current availability and prices; prioritize manufacturer specifications, manuals, reliable independent tests, and actual retailer listings. Never invent a specification, discount, stock status, fee, or review.
- Compare equivalent configurations, capacity, quantity, generation, accessories, seller, and warranty. Normalize pack prices to a per-unit price (per kg, litre, item, or inner unit) and distinguish marketplace sellers from the manufacturer.
- Separate verified facts, merchant claims, measured results, estimates, and missing evidence. Treat rankings, affiliate articles, star averages, and unverified claims critically.
- Prices, offers, fees, and stock are time-bound: record the retrieval date for each, check offer validity windows, and never present an indexed, cached, or remembered price as current.
- Never purchase, subscribe, place an order, contact a seller, bypass authentication or access controls, or expose private household information (address, membership number, payment data, credentials) without an explicit user request.

## Store and channel profiles

When the purchase involves a specific retailer or channel, load its profile from `references/` if one exists and apply it on top of this workflow. A profile records stable facts only: official sources, how the catalog and offers are published, what requires a session or postcode, fee and minimum-order structure, membership rules, and search tips. It never stores live prices or offer dates. Use `references/channel-profiles.md` for the profile template and the shared cost models; when no profile exists, gather the same fields from official sources before comparing.

Available profiles:

- [Costco España, warehouse and Costco Same-Day (Instacart Storefront)](references/costco-es.md).

## Workflow

1. Identify the real use case and derive non-negotiable requirements. Ask only for missing details that could change the recommendation; otherwise state reasonable assumptions and continue. For baskets, confirm the list, quantities, acceptable substitutions, and which store or warehouse and postcode area the user chooses, without asking for a full address.
2. Inspect supplied links, exact model numbers or SKUs, variants, pack formats, accessories, compatibility, and product dimensions. Resolve shortened links when possible. Separate purchase units from inner units of a pack.
3. Find meaningful alternatives across manufacturers, product categories, trustworthy sellers, and purchase channels (online delivery, same-day delivery, pickup, in-store visit). Include the user's candidate and a no-purchase alternative when relevant.
4. Validate current purchase conditions: item price with retrieval date, offer validity window, shipping or delivery fee, service fee, minimum order, taxes, returns, warranty, seller reputation, regional or postcode availability, substitution policy, and whether consumables are included. Discard expired offers; mark values hidden behind a session, membership, or postcode as pending instead of guessing.
5. Estimate total cost: for durable goods, total cost of ownership over an appropriate horizon (consumables, replacement parts, energy, subscriptions, maintenance, installation, required accessories); for baskets and channels, apply the channel cost model and membership amortization in `references/channel-profiles.md`, penalizing filler items added only to reach a minimum.
6. Check real-world fit: measurements, noise, electrical requirements, existing ecosystem, network protocols, repairability, storage space, perishability, cold-chain transport, and foreseeable upgrades. Do not confuse theoretical throughput or marketing labels with observed performance.
7. Compare independent evidence and flag uncertain specifications, suspicious or expired discounts, price differences between channels for the same SKU, fake-review patterns, lock-in, short support periods, and products or pack sizes that are oversized for the actual need.
8. Rank options by value for this user's constraints, explain tradeoffs, show how sensitive the ranking is to unknown fees or travel cost, and identify what new information would change the answer.

## Output

Use a concise comparison table when at least two viable options exist. Include exact model or SKU and format, verified price, per-unit price when packs differ, seller or channel, retrieval date, offer status and end date, essential differentiators, compatibility, ownership or channel costs when meaningful, and limitations. Link directly to supporting sources. Separate confirmed costs from pending ones. End with one primary recommendation, one lower-cost or alternative-category option when useful, reasons not to buy the rejected candidates, and a clear statement when waiting or buying nothing is the best choice.
