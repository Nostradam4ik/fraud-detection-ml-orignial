# Outputs for Fraud Detection Infrastructure
#
# Author: Zhmuryk Andrii
# Copyright (c) 2024 - All Rights Reserved

# VPC Outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

output "alb_url" {
  description = "Full URL of the Application Load Balancer"
  value       = "https://${module.ecs.alb_dns_name}"
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.port
}

# ElastiCache Outputs
output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.endpoint
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.elasticache.port
}

# S3 Outputs
output "s3_models_bucket" {
  description = "S3 bucket for ML models"
  value       = module.s3.models_bucket_name
}

output "s3_backups_bucket" {
  description = "S3 bucket for backups"
  value       = module.s3.backups_bucket_name
}

# Monitoring Outputs
output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.monitoring.dashboard_url
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = module.monitoring.sns_topic_arn
}

# Summary
output "deployment_summary" {
  description = "Summary of the deployment"
  value = {
    environment  = var.environment
    region       = var.aws_region
    alb_url      = "https://${module.ecs.alb_dns_name}"
    cluster_name = module.ecs.cluster_name
  }
}
