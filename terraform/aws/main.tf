# ROSTR Agent Framework — AWS Infrastructure
# Advanced V2 One-Click Setup

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

resource "aws_instance" "rostr_agent" {
  ami           = "ami-0e86e20dae9224db8" # Ubuntu 24.04 LTS
  instance_type = "t3.medium"

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update
              sudo apt-get install -y nodejs npm git
              curl -fsSL https://ollama.com/install.sh | sh
              git clone https://github.com/diamitani/rostr-agent.git
              cd rostr-agent
              npm install
              # Start ROSTR as a service
              npm run serve &
              EOF

  tags = {
    Name = "ROSTR-Agent-OS"
  }
}

output "public_ip" {
  value = aws_instance.rostr_agent.public_ip
}
