# ⚡ Cloud Function SaaS

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Run-4285f4.svg)](https://cloud.google.com/run)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%20AI-orange.svg)](https://www.anthropic.com/claude)

_Transform specification documents into deployed Google Cloud Run microservices with AI_

[Quick Start](#-quick-start) • [Examples](examples/) • [Documentation](docs/) • [Contributing](docs/contributing.md)

</div>

---

## 🚀 What is Cloud Function SaaS?

Cloud Function SaaS is an AI-powered tool that converts simple markdown specifications into fully deployed Google Cloud Run microservices. Write your API specification in plain English, and let a team of AI agents generate, validate, and deploy.

### ✨ Key Features

- 📝 **Simple Specs**: Write APIs in markdown format
- 🤖 **Multi-Agent AI**: Team of specialized agents for code generation, validation, and testing
- 🎯 **Quality Gates**: Automatic validation ensures 90%+ deployment success rate
- ☁️ **Auto-Deploy**: Direct deployment to Google Cloud Run in under 2 minutes
- 🔧 **Multi-Language**: Support for Node.js, Python, Go (planned)
- ✅ **Spec Compliance**: Generated code automatically validated against your requirements

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **Google Cloud SDK** ([Installation Guide](https://cloud.google.com/sdk/docs/install)) OR **Service Account Key** for Docker deployments
- **Anthropic API key** ([Get yours here](https://console.anthropic.com/))
- **Google Cloud project** with Cloud Run enabled

### Installation

#### 🐳 Option 1: Docker

```bash
# Clone and set up
git clone https://github.com/boxwood-ai/cloud-function-saas.git
cd cloud-function-saas

# Create environment file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
echo "GOOGLE_CLOUD_PROJECT=your-gcp-project-id" >> .env

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project your-gcp-project-id

# Deploy your first service
docker-compose run --rm cloud-function-saas specs/examples/01-hello-world.md --verbose
```

#### 🐍 Option 2: Local Python (Recommended)

```bash
git clone https://github.com/boxwood-ai/cloud-function-saas.git
cd cloud-function-saas
pip install -r requirements.txt

# Set up environment
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
echo "GOOGLE_CLOUD_PROJECT=your-gcp-project-id" >> .env

# Configure Google Cloud
gcloud auth login
gcloud config set project your-gcp-project-id

# Deploy your first service
python prototype.py specs/examples/01-hello-world.md --verbose
```

### Your First Deployment

```bash
# Validate setup
python prototype.py specs/template.md --validate-only

# Deploy with multi-agent generation (default)
python prototype.py specs/template.md --verbose

# Test your deployed service
curl https://your-service-url.run.app/users
```

## 📋 Writing Specifications

Simple specs in just 20-50 lines of markdown:

```markdown
# Service Name: My API Service
Description: What your service does in one line
Runtime: Node.js 20

## Endpoints

### GET /items
- Description: List all items
- Output: { items: array }

### POST /items
- Description: Create new item
- Input: { name: string, value: number }
- Output: { item: Item, id: string }

## Models

### Item
- id: string (auto-generated)
- name: string (required)
- value: number
- createdAt: timestamp
```

**📝 Start here:** [Template Spec](specs/template.md) - Copy and customize!

**Example Specifications:**

- [Hello World](specs/examples/01-hello-world.md) - Simplest API (12 lines)
- [Todo List](specs/examples/02-todo-list.md) - CRUD operations (30 lines)
- [Email Service](specs/examples/03-email-sender.md) - Send notifications (23 lines)
- [Auth Service](specs/examples/06-auth-basic.md) - JWT authentication (28 lines)
- [More examples...](specs/examples/)

## 🔐 Authentication

Supports multiple authentication methods with automatic detection:

| Method                     | Use Case                  | Setup                                |
| -------------------------- | ------------------------- | ------------------------------------ |
| **🖥️ gcloud CLI**          | Local development         | `gcloud auth login`                  |
| **🔑 Service Account Key** | Docker, CI/CD, Production | Set `GOOGLE_APPLICATION_CREDENTIALS` |

## ⚙️ Configuration

Create a `.env` file in your project root:

```env
# Required
ANTHROPIC_API_KEY=your_claude_api_key
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Optional
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GOOGLE_CLOUD_REGION=us-central1
```

### Command Options

```bash
python prototype.py <spec-file> [options]

# Options
--project           Override GCP project
--region           Override deployment region
--output-dir       Keep generated files
--validate-only    Check setup without deploying
--verbose, -v      Detailed output
--multi-agent      Force multi-agent mode (default)
--single-agent     Use classic single-agent mode
```

## 📖 Documentation

- [Multi-Agent System Guide](docs/multi-agent-system.md)
- [Project Goals & Vision](docs/goals.md)
- [Writing Specifications](docs/specifications.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing Guide](docs/contributing.md)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

[⭐ Star this repo](https://github.com/boxwood-ai/cloud-function-saas) • [🍴 Fork it](https://github.com/boxwood-ai/cloud-function-saas/fork) • [🐛 Report Issues](https://github.com/boxwood-ai/cloud-function-saas/issues)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=boxwood-ai/cloud-function-saas&type=Date)](https://star-history.com/#boxwood-ai/cloud-function-saas&Date)

</div>
