# SautiRelay Product Brief

## Name

The product name is **SautiRelay**. The repository, package names, and service identifiers should use lowercase `sautirelay`.

## Problem

People often see early warning signs before institutions can respond: local conflict tension, civic harm, public service gaps, displacement pressure, aid diversion, GBV referral needs, or other community risks. Reporting these concerns can expose the reporter to retaliation or social harm. SautiRelay gives communities a safer way to raise signals and route them to the right responders with only the necessary context.

## Product Objective

SautiRelay turns a raw community report into a structured, privacy-preserving relay item that can be reviewed, triaged, and escalated. The platform should protect reporter identity by default, collect location only with clear purpose and consent, and support expansion beyond peacebuilding into wider community accountability workflows.

## MVP Users

- Community reporter: submits a concern without needing to reveal identity.
- Verifier: reviews structured relay items and checks whether escalation is appropriate.
- Responder: receives routed reports and acts through an existing community, civil society, or support channel.
- Administrator: configures local categories, responder routes, and safety policies in future phases.

## MVP Capabilities

- Anonymous report capture.
- Approximate or manual location capture with no precise location by default.
- Structured relay result with category, urgency, summary, safety notes, and recommended route.
- Local-only backend and frontend workflow.
- Documentation-first architecture so implementation can proceed safely.

## Privacy Principles

- Collect the minimum information needed for routing.
- Prefer approximate location over precise coordinates.
- Separate reporter identity from report content if optional contact details are introduced later.
- Redact names, phone numbers, and other sensitive identifiers before escalation.
- Make consent explicit when requesting location or optional follow-up contact.

## Non-Goals

- Production deployment.
- Real responder onboarding.
- Live AI provider integration.
- Identity verification.
- Long-term storage of reports.
- Automated emergency dispatch.

## Tagline

SautiRelay - Safe community signals for early action.
