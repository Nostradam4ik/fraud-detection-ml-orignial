# S3 Module - Object Storage
# Creates S3 buckets for ML models and backups

variable "name_prefix" {
  type = string
}

variable "random_suffix" {
  type = string
}

variable "environment" {
  type = string
}

# S3 Bucket for ML Models
resource "aws_s3_bucket" "models" {
  bucket = "${var.name_prefix}-models-${var.random_suffix}"

  tags = {
    Name = "${var.name_prefix}-models"
    Type = "ml-models"
  }
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket = aws_s3_bucket.models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for Backups
resource "aws_s3_bucket" "backups" {
  bucket = "${var.name_prefix}-backups-${var.random_suffix}"

  tags = {
    Name = "${var.name_prefix}-backups"
    Type = "backups"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rules for backups
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "archive-old-backups"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 Bucket for Logs (optional)
resource "aws_s3_bucket" "logs" {
  bucket = "${var.name_prefix}-logs-${var.random_suffix}"

  tags = {
    Name = "${var.name_prefix}-logs"
    Type = "logs"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    expiration {
      days = 90
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Outputs
output "models_bucket_name" {
  value = aws_s3_bucket.models.bucket
}

output "models_bucket_arn" {
  value = aws_s3_bucket.models.arn
}

output "backups_bucket_name" {
  value = aws_s3_bucket.backups.bucket
}

output "backups_bucket_arn" {
  value = aws_s3_bucket.backups.arn
}

output "logs_bucket_name" {
  value = aws_s3_bucket.logs.bucket
}
