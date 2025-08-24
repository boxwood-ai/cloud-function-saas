# AWS ECS Fargate Module Outputs

output "service_url" {
  description = "URL of the load balancer"
  value       = "http://${aws_lb.main.dns_name}"
}

output "service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = var.create_ecs_cluster ? aws_ecs_cluster.main[0].name : var.ecs_cluster_name
}

output "task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = aws_ecs_task_definition.app.arn
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.app.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository (if created)"
  value       = var.create_ecr_repository ? aws_ecr_repository.app[0].repository_url : null
}

output "ecr_repository_name" {
  description = "Name of the ECR repository (if created)"
  value       = var.create_ecr_repository ? aws_ecr_repository.app[0].name : null
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
}

output "subnet_ids" {
  description = "IDs of the subnets"
  value       = var.create_vpc ? aws_subnet.public[*].id : var.subnet_ids
}

output "security_group_id" {
  description = "ID of the ECS service security group"
  value       = aws_security_group.ecs_service.id
}

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "cloudwatch_log_group" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app.name
}

output "deployment_info" {
  description = "Comprehensive deployment information"
  value = {
    service_url        = "http://${aws_lb.main.dns_name}"
    service_name       = aws_ecs_service.app.name
    cluster_name       = var.create_ecs_cluster ? aws_ecs_cluster.main[0].name : var.ecs_cluster_name
    region            = var.aws_region
    container_image   = var.container_image
    environment       = var.environment
    load_balancer_dns = aws_lb.main.dns_name
    deployed_at       = timestamp()
  }
}