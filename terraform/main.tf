# Fraud Detection ML System - AWS Infrastructure
# Terraform configuration for production deployment
#
# Author: Zhmuryk Andrii
# Copyright (c) 2024 - All Rights Reserved

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Backend configuration - uncomment for production
  # backend "s3" {
  #   bucket         = "fraud-detection-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "eu-west-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "fraud-detection"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "Zhmuryk Andrii"
    }
  }
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix = "fraud-${var.environment}"
  common_tags = {
    Project     = "fraud-detection"
    Environment = var.environment
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  environment        = var.environment
}

# Security Groups Module
module "security" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  environment = var.environment
}

# RDS Module (PostgreSQL)
module "rds" {
  source = "./modules/rds"

  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security.rds_security_group_id

  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_name              = var.db_name
  db_username          = var.db_username
  db_password          = var.db_password

  environment = var.environment
}

# ElastiCache Module (Redis)
module "elasticache" {
  source = "./modules/elasticache"

  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security.redis_security_group_id

  node_type       = var.redis_node_type
  num_cache_nodes = var.redis_num_nodes

  environment = var.environment
}

# ECS Cluster Module
module "ecs" {
  source = "./modules/ecs"

  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids

  ecs_security_group_id = module.security.ecs_security_group_id
  alb_security_group_id = module.security.alb_security_group_id

  # Backend configuration
  backend_image         = var.backend_image
  backend_cpu           = var.backend_cpu
  backend_memory        = var.backend_memory
  backend_desired_count = var.backend_desired_count

  # Frontend configuration
  frontend_image         = var.frontend_image
  frontend_cpu           = var.frontend_cpu
  frontend_memory        = var.frontend_memory
  frontend_desired_count = var.frontend_desired_count

  # Environment variables
  database_url = module.rds.connection_string
  redis_url    = module.elasticache.connection_string

  environment = var.environment
}

# S3 Module (for ML models and backups)
module "s3" {
  source = "./modules/s3"

  name_prefix   = local.name_prefix
  random_suffix = random_id.suffix.hex
  environment   = var.environment
}

# CloudWatch Module (Monitoring)
module "monitoring" {
  source = "./modules/monitoring"

  name_prefix     = local.name_prefix
  ecs_cluster_arn = module.ecs.cluster_arn
  alb_arn_suffix  = module.ecs.alb_arn_suffix
  rds_identifier  = module.rds.db_identifier

  alarm_email = var.alarm_email
  environment = var.environment
}

# WAF Module (Web Application Firewall)
module "waf" {
  source = "./modules/waf"

  name_prefix = local.name_prefix
  alb_arn     = module.ecs.alb_arn
  environment = var.environment
}

# Route53 Module (DNS) - Optional
# module "dns" {
#   source = "./modules/dns"
#
#   domain_name    = var.domain_name
#   alb_dns_name   = module.ecs.alb_dns_name
#   alb_zone_id    = module.ecs.alb_zone_id
#   environment    = var.environment
# }
