# Future Infrastructure Notes

This directory is for future SautiRelay infrastructure documentation only.

## Current Boundary

Do not add deployment scripts, Terraform, CloudFormation, CDK, serverless configs, or GitHub deployment workflows yet. The current project phase is local development and testing.

## Planned AWS Shape

- Frontend: S3 + CloudFront.
- Backend: Lambda + API Gateway.
- Persistence: managed database or object storage after the local relay model is validated.
- Async routing: queue or notification service for responder handoff.
- Secrets: managed secret storage, not committed environment files.

## Open Questions

- Which African regions and responder networks are in the first pilot?
- What data retention policy applies to relay records?
- What level of location precision is acceptable?
- Which communication channels should be supported first: web, SMS, USSD, WhatsApp, or mobile app?
- What human verification process is required before responder escalation?
