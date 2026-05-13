# Infrastructure Notes

This directory contains the first AWS deployment path for SautiRelay.

## AWS Shape

- Frontend: static SvelteKit build in a private S3 bucket, served through CloudFront with Origin Access Control.
- Backend: FastAPI packaged as an AWS Lambda container image in ECR, exposed through API Gateway HTTP API.
- Persistence: DynamoDB single-table storage for application documents.
- Embeddings: S3 Vectors vector bucket and index.
- Deploy runner: GitHub Actions, authenticated with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets.

## Configuration

Keep the root `.env` file local and uncommitted. Configure non-secret deployment values as GitHub repository Variables. The workflow also reads `infra/deploy.env` if present, so that file can be used for local deployment-only overrides. Keep production secrets in GitHub Secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `JWT_SECRET`
- `VERIFIER_PASSWORD`
- `MEDIATOR_PASSWORD`

Terraform lives in `infra/terraform`. The deployment workflow first creates the ECR repository, then builds and pushes the Lambda image from GitHub Actions, then applies the complete stack.
