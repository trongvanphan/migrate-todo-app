# Strangler-fig routing — {{DOMAIN}}
# AWS ALB weighted target groups.
# Apply with: terraform plan -var ramp_percent={{RAMP_PERCENT}} && terraform apply

variable "ramp_percent" {
  description = "Percent of traffic to send to new"
  type        = number
  default     = 0
  validation {
    condition     = var.ramp_percent >= 0 && var.ramp_percent <= 100
    error_message = "ramp_percent must be between 0 and 100."
  }
}

variable "domain_name"  { type = string  default = "{{DOMAIN}}" }
variable "vpc_id"       { type = string }
variable "listener_arn" { type = string  description = "ARN of the ALB listener" }

resource "aws_lb_target_group" "legacy" {
  name        = "${var.domain_name}-legacy"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/api/${var.domain_name}/health"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200-299"
  }

  deregistration_delay = 30
}

resource "aws_lb_target_group" "new" {
  name        = "${var.domain_name}-new"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/api/${var.domain_name}/health"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200-299"
  }

  deregistration_delay = 30
}

resource "aws_lb_listener_rule" "domain_routing" {
  listener_arn = var.listener_arn
  priority     = 100

  condition {
    path_pattern {
      values = ["/api/${var.domain_name}/*"]
    }
  }

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.legacy.arn
        weight = 100 - var.ramp_percent
      }
      target_group {
        arn    = aws_lb_target_group.new.arn
        weight = var.ramp_percent
      }

      stickiness {
        enabled  = true
        duration = 3600
      }
    }
  }
}

output "current_ramp_percent" {
  value = var.ramp_percent
}
