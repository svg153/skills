---
name: home-assistant-smart-home-planner
description: "Design and evaluate Home Assistant installations, device choices, smart-home protocols, room sensors, automations, voice control, networking, power resilience, backups, and migrations. Use when the user asks about Home Assistant hardware, Zigbee, Thread, Matter, Wi-Fi, Bluetooth, coordinators, blinds, environmental monitoring, local voice, NAS hosting, or phased smart-home purchasing."
---

# Home Assistant Smart Home Planner

## Architecture principles

- Optimize for reliability, local operation, interoperability, maintainability, recoverability, and the user's tolerance for complexity. Do not recommend self-hosting merely because equipment is available.
- Discover the real constraints: property layout, construction, equipment placement, wired network availability, electrical permissions, existing devices, expected uptime, noise, power resilience, household needs, and budget.
- Verify device support against current official documentation, integration pages, manufacturer specifications, and reputable interoperability databases. Distinguish announced features from working support.
- Never claim Zigbee, Thread, Matter, Bluetooth, or Wi-Fi compatibility from branding alone. Confirm radio protocol, role, hub requirements, firmware, local APIs, supported clusters or capabilities, and region.
- Treat access credentials, floor plans, physical security details, camera feeds, presence history, and household routines as private. Request only what is needed and do not embed sensitive details in public artifacts.
- Do not instruct unqualified users to work on mains wiring. Recommend a qualified electrician when switch, shutter, neutral-wire, or protection-circuit work requires one.

## Planning workflow

1. Inventory existing controller candidates, network equipment, devices, hubs, automations, and services; identify which investments can be reused safely.
2. Compare deployment options such as dedicated appliances, virtual machines, containers, and existing NAS or mini-PC hardware. Include add-on availability, USB or network radio support, updates, restart behavior, backup portability, idle power, noise, and failure domains.
3. Choose protocols per use case rather than declaring a universal winner. Plan coordinator location, powered routers, mesh density, interference, radio separation, Bluetooth proxies, Ethernet backhaul, and coverage verification.
4. Define per-room sensor requirements and realistic accuracy: temperature, humidity, CO2, particulates, occupancy, illuminance, battery life, display, and historical retention. Explain which quantities a device cannot measure.
5. For shutters, lighting, and switches, verify motor type, physical control wiring, neutral availability, safety interlocks, calibration, manual fallback, and behavior after a controller outage.
6. Design local-first voice and automations only where they add value; explain microphones, wake-word behavior, speech processing, cloud dependencies, privacy, response latency, and failure behavior.
7. Plan encrypted backups, tested restoration, migration between hardware, UPS requirements, restart ordering, remote-access security, update strategy, and separation from unrelated experimental services.
8. Deliver the system in phases: minimum reliable foundation, representative pilot, measured coverage and usability, broader rollout, and optional advanced capabilities.

## Output

Provide a concise topology or decision table when it clarifies the design, exact compatibility checks, a prioritized purchase list, viable alternatives, phased installation and validation steps, expected recurring costs, migration and backup strategy, and the main reasons to reject tempting but fragile options.
