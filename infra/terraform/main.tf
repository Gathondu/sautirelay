data "aws_caller_identity" "current" {}

locals {
  name_prefix = lower("${var.project_name}-${var.environment}")
  account_id  = data.aws_caller_identity.current.account_id

  frontend_bucket_name = coalesce(var.frontend_bucket_name, "${local.name_prefix}-frontend-${local.account_id}")
  lambda_function_name = coalesce(var.lambda_function_name, "${local.name_prefix}-api")
  dynamodb_table_name  = coalesce(var.dynamodb_table_name, "${local.name_prefix}-app")
  vector_bucket_name   = coalesce(var.s3_vector_bucket_name, "${local.name_prefix}-vectors-${local.account_id}")

  lambda_environment = {
    ENV                             = var.environment
    SAUTIRELAY_AWS_REGION           = var.aws_region
    REPOSITORY_BACKEND              = "dynamodb"
    DYNAMODB_TABLE_NAME             = aws_dynamodb_table.app.name
    S3_VECTOR_BUCKET_NAME           = aws_s3vectors_vector_bucket.embeddings.vector_bucket_name
    S3_VECTOR_INDEX_NAME            = aws_s3vectors_index.report_embeddings.index_name
    OPENAI_MODEL                    = var.openai_model
    OPENAI_BASE_URL                 = var.openai_base_url
    OPENAI_MAX_OUTPUT_TOKENS        = tostring(var.openai_max_output_tokens)
    EMBEDDING_MODEL                 = var.embedding_model
    EMBEDDING_DIMENSIONS            = tostring(var.embedding_dimensions)
    EMBEDDING_INPUT_TYPE            = var.embedding_input_type
    EMBEDDING_EXTRA_BODY            = var.embedding_extra_body
    EMBEDDING_EXTRA_HEADERS         = var.embedding_extra_headers
    CORS_ALLOW_ORIGINS              = var.cors_allow_origins
    CORS_ALLOW_CREDENTIALS          = var.cors_allow_credentials
    CORS_ALLOW_METHODS              = var.cors_allow_methods
    CORS_ALLOW_HEADERS              = var.cors_allow_headers
    DEMO_SEED_ENABLED               = var.demo_seed_enabled
    DEMO_SEED_WITH_AI               = var.demo_seed_with_ai
    AI_ALLOW_DETERMINISTIC_FALLBACK = var.ai_allow_deterministic_fallback
    VERIFIER_USERNAME               = var.verifier_username
    MEDIATOR_USERNAME               = var.mediator_username
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name_prefix}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_dynamodb_table" "app" {
  name         = local.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  attribute {
    name = "GSI2PK"
    type = "S"
  }

  attribute {
    name = "GSI2SK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    projection_type = "ALL"

    key_schema {
      attribute_name = "GSI1PK"
      key_type       = "HASH"
    }

    key_schema {
      attribute_name = "GSI1SK"
      key_type       = "RANGE"
    }
  }

  global_secondary_index {
    name            = "GSI2"
    projection_type = "ALL"

    key_schema {
      attribute_name = "GSI2PK"
      key_type       = "HASH"
    }

    key_schema {
      attribute_name = "GSI2SK"
      key_type       = "RANGE"
    }
  }
}

resource "aws_s3vectors_vector_bucket" "embeddings" {
  vector_bucket_name = local.vector_bucket_name
}

resource "aws_s3vectors_index" "report_embeddings" {
  vector_bucket_name = aws_s3vectors_vector_bucket.embeddings.vector_bucket_name
  index_name         = var.s3_vector_index_name
  data_type          = "float32"
  dimension          = var.embedding_dimensions
  distance_metric    = "cosine"
}

resource "aws_s3_bucket" "frontend" {
  bucket = local.frontend_bucket_name
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  description                       = "CloudFront access to the private SautiRelay frontend bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${local.name_prefix} frontend"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "frontend-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "frontend-s3"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/200.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/200.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

data "aws_iam_policy_document" "frontend_bucket" {
  statement {
    sid     = "AllowCloudFrontRead"
    actions = ["s3:GetObject"]

    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket.json
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.name_prefix}-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_data" {
  statement {
    actions = [
      "dynamodb:DeleteItem",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:UpdateItem",
    ]

    resources = [
      aws_dynamodb_table.app.arn,
      "${aws_dynamodb_table.app.arn}/index/*",
    ]
  }

  statement {
    actions = [
      "s3vectors:GetVectors",
      "s3vectors:PutVectors",
      "s3vectors:QueryVectors",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda_data" {
  name   = "${local.name_prefix}-lambda-data"
  policy = data.aws_iam_policy_document.lambda_data.json
}

resource "aws_iam_role_policy_attachment" "lambda_data" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda_data.arn
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 30
}

resource "aws_lambda_function" "backend" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.backend_image_uri
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout_seconds

  environment {
    variables = local.lambda_environment
  }

  depends_on = [
    aws_cloudwatch_log_group.backend,
    aws_iam_role_policy_attachment.lambda_logs,
    aws_iam_role_policy_attachment.lambda_data,
  ]
}

resource "aws_apigatewayv2_api" "backend" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["Authorization", "Content-Type"]
    allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_origins = split(",", var.cors_allow_origins)
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_integration" "backend" {
  api_id                 = aws_apigatewayv2_api.backend.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "backend" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_stage" "backend" {
  api_id      = aws_apigatewayv2_api.backend.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*/*"
}
