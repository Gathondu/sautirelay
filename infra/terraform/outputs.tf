output "api_endpoint" {
  description = "API Gateway HTTP API endpoint."
  value       = aws_apigatewayv2_api.backend.api_endpoint
}

output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL."
  value       = aws_ecr_repository.backend.repository_url
}

output "backend_lambda_function_name" {
  description = "Backend Lambda function name."
  value       = aws_lambda_function.backend.function_name
}

output "cloudfront_distribution_id" {
  description = "Frontend CloudFront distribution ID."
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "Frontend CloudFront domain name."
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_bucket_name" {
  description = "Frontend S3 bucket name."
  value       = aws_s3_bucket.frontend.bucket
}

output "dynamodb_table_name" {
  description = "DynamoDB table name."
  value       = aws_dynamodb_table.app.name
}

output "s3_vector_bucket_name" {
  description = "S3 Vectors bucket name."
  value       = aws_s3vectors_vector_bucket.embeddings.vector_bucket_name
}

output "s3_vector_index_name" {
  description = "S3 Vectors index name."
  value       = aws_s3vectors_index.report_embeddings.index_name
}
