# SautiRelay User Flows

## Submit A Community Signal

1. Reporter opens SautiRelay.
2. Reporter describes the concern in plain language.
3. Reporter selects a category if known, or leaves category as "unsure".
4. Reporter selects an urgency hint.
5. Reporter chooses a location mode: none, manual, or approximate with consent.
6. Reporter submits the report.
7. UI shows a structured report result with category, urgency, anonymized summary, safety notes, and recommended route.

## Location Consent Flow

1. Reporter chooses approximate location.
2. UI explains that location is used only for routing.
3. Reporter grants or denies browser location permission.
4. If granted, the app sends generalized location data.
5. If denied, the app offers manual location text or no location.

## Validation Error Flow

1. Reporter submits incomplete or invalid data.
2. Backend returns validation details.
3. UI highlights the relevant fields and presents an error summary.
4. Reporter corrects the input and resubmits.

## Backend Unavailable Flow

1. Reporter submits the form.
2. API request fails or times out.
3. UI keeps the entered report text in place.
4. UI shows a retry option and a clear service-unavailable message.

## Future Verification Flow

1. Verifier receives a structured report item.
2. Verifier checks sensitivity, duplicate reports, location confidence, and urgency.
3. Verifier selects a responder route or marks the report for more context.
4. Responder receives only the information needed to act safely.

## Future Status Flow

1. Reporter receives a non-identifying reference code.
2. Reporter can check whether the report was received, reviewed, or routed.
3. Status never exposes responder identity or sensitive investigation details.
