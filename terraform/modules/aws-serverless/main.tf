# AWS ECS Fargate Serverless Module
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC and Networking
resource "aws_vpc" "main" {
  count                = var.create_vpc ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.service_name}-vpc"
    Service     = var.service_name
    Environment = var.environment
    ManagedBy   = "cloud-function-saas"
  }
}

resource "aws_internet_gateway" "main" {
  count  = var.create_vpc ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  tags = {
    Name        = "${var.service_name}-igw"
    Service     = var.service_name
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count                   = var.create_vpc ? 2 : 0
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.service_name}-public-${count.index + 1}"
    Service     = var.service_name
    Environment = var.environment
  }
}

resource "aws_route_table" "public" {
  count  = var.create_vpc ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = {
    Name        = "${var.service_name}-public-rt"
    Service     = var.service_name
    Environment = var.environment
  }
}

resource "aws_route_table_association" "public" {
  count          = var.create_vpc ? length(aws_subnet.public) : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

# Security Groups
resource "aws_security_group" "ecs_service" {
  name        = "${var.service_name}-ecs-sg"
  description = "Security group for ${var.service_name} ECS service"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id

  ingress {
    from_port   = var.container_port
    to_port     = var.container_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.service_name}-ecs-sg"
    Service     = var.service_name
    Environment = var.environment
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.service_name}-alb-sg"
  description = "Security group for ${var.service_name} ALB"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.service_name}-alb-sg"
    Service     = var.service_name
    Environment = var.environment
  }
}

# ECR Repository
resource "aws_ecr_repository" "app" {
  count        = var.create_ecr_repository ? 1 : 0
  name         = var.service_name
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Service     = var.service_name
    Environment = var.environment
    ManagedBy   = "cloud-function-saas"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  count = var.create_ecs_cluster ? 1 : 0
  name  = var.service_name

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = {
    Service     = var.service_name
    Environment = var.environment
    ManagedBy   = "cloud-function-saas"
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.service_name}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Service     = var.service_name
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task" {
  name = "${var.service_name}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Service     = var.service_name
    Environment = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.service_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Service     = var.service_name
    Environment = var.environment
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = var.service_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu_units
  memory                   = var.memory_units
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = var.service_name
      image = var.container_image
      
      portMappings = [
        {
          containerPort = var.container_port
          protocol     = "tcp"
        }
      ]

      environment = [
        for key, value in var.environment_variables : {
          name  = key
          value = value
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:${var.container_port}${var.health_check_path} || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      essential = true
    }
  ])

  tags = {
    Service     = var.service_name
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.service_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = var.create_vpc ? aws_subnet.public[*].id : var.subnet_ids

  enable_deletion_protection = false

  tags = {
    Service     = var.service_name
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "app" {
  name        = "${var.service_name}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path               = var.health_check_path
    matcher            = "200"
    protocol           = "HTTP"
  }

  tags = {
    Service     = var.service_name
    Environment = var.environment
  }
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = var.service_name
  cluster         = var.create_ecs_cluster ? aws_ecs_cluster.main[0].id : var.ecs_cluster_name
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_service.id]
    subnets         = var.create_vpc ? aws_subnet.public[*].id : var.subnet_ids
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.service_name
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.app]

  tags = {
    Service     = var.service_name
    Environment = var.environment
  }
}