variable "project_name" {
  description = "Short project name used in AWS resource names."
  type        = string
  default     = "sautirelay"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for regional resources. Must support S3 Vectors."
  type        = string
  default     = "af-south-1"
}

variable "backend_image_uri" {
  description = "Fully qualified ECR image URI for the Lambda backend image."
  type        = string
}

variable "frontend_bucket_name" {
  description = "Optional globally unique S3 bucket name for the frontend."
  type        = string
  default     = null
}

variable "lambda_function_name" {
  description = "Optional Lambda function name."
  type        = string
  default     = null
}

variable "dynamodb_table_name" {
  description = "Optional DynamoDB table name."
  type        = string
  default     = null
}

variable "s3_vector_bucket_name" {
  description = "Optional S3 Vectors vector bucket name."
  type        = string
  default     = null
}

variable "s3_vector_index_name" {
  description = "S3 Vectors index name for report embeddings."
  type        = string
  default     = "report-embeddings"
}

variable "embedding_dimensions" {
  description = "Embedding dimension count configured on the S3 Vectors index."
  type        = number
  default     = 1536
}

variable "openai_model" {
  description = "OpenAI model used for AI intake."
  type        = string
  default     = "gpt-5.5"
}

variable "openai_base_url" {
  description = "Optional OpenAI-compatible base URL."
  type        = string
  default     = ""
}

variable "openai_max_output_tokens" {
  description = "Maximum output tokens for AI intake."
  type        = number
  default     = 1200
}

variable "embedding_model" {
  description = "OpenAI embedding model used for report embeddings."
  type        = string
  default     = "text-embedding-3-small"
}

variable "embedding_input_type" {
  description = "Optional provider-specific embedding input type."
  type        = string
  default     = ""
}

variable "embedding_extra_body" {
  description = "JSON object string with provider-specific embedding request body fields."
  type        = string
  default     = "{}"
}

variable "embedding_extra_headers" {
  description = "JSON object string with provider-specific embedding request headers."
  type        = string
  default     = "{}"
}

variable "cors_allow_origins" {
  description = "Comma-separated CORS allow-origin list. GitHub Actions sets this after CloudFront exists."
  type        = string
  default     = "*"
}

variable "cors_allow_credentials" {
  description = "Whether backend CORS allows credentials."
  type        = string
  default     = "false"
}

variable "cors_allow_methods" {
  description = "Comma-separated backend CORS methods."
  type        = string
  default     = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
}

variable "cors_allow_headers" {
  description = "Comma-separated backend CORS headers."
  type        = string
  default     = "Authorization,Content-Type"
}

variable "demo_seed_enabled" {
  description = "Whether production Lambda should seed demo data."
  type        = string
  default     = "false"
}

variable "demo_seed_with_ai" {
  description = "Whether demo seeding may call AI."
  type        = string
  default     = "false"
}

variable "ai_allow_deterministic_fallback" {
  description = "Whether production AI paths may use deterministic fallback."
  type        = string
  default     = "false"
}

variable "verifier_username" {
  description = "Verifier login username."
  type        = string
  default     = "verifier@sautirelay.dev"
}

variable "mediator_username" {
  description = "Mediator login username."
  type        = string
  default     = "mediator@sautirelay.dev"
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB."
  type        = number
  default     = 1024
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 60
}
