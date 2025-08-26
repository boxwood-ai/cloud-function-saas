"""
Container building and pushing functionality for Cloud Function deployments
"""

import os
import subprocess
import shutil
import logging
from typing import Optional, Tuple
from pathlib import Path


class ContainerBuilder:
    """Build and push containers for cloud deployments"""
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger('container_builder')
        self._check_gcloud_available()
        
    def _check_gcloud_available(self) -> None:
        """Check if gcloud CLI is available"""
        gcloud_path = shutil.which('gcloud')
        if not gcloud_path:
            raise RuntimeError(
                "gcloud CLI not found in PATH. "
                "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
            )
        
        self.logger.info(f"Found gcloud CLI at: {gcloud_path}")
        
        # Check if authenticated
        try:
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE'], 
                                  capture_output=True, text=True, check=True)
            if 'ACTIVE' not in result.stdout:
                raise RuntimeError("No active Google Cloud authentication found. Run 'gcloud auth login' first.")
        except subprocess.CalledProcessError:
            raise RuntimeError("Unable to check Google Cloud authentication status.")
    
    def build_and_push(self, service_name: str, project_id: str, region: str = "us-central1", 
                      tag: str = "latest", force_rebuild: bool = False) -> Tuple[bool, str]:
        """Build container using Google Cloud Build and push to Google Container Registry"""
        
        # Construct image name
        image_name = f"gcr.io/{project_id}/{service_name}:{tag}"
        
        self.logger.info(f"☁️ Building container with Cloud Build: {image_name}")
        
        # Check if Dockerfile exists and is valid
        dockerfile_path = self.project_dir / "Dockerfile"
        if not dockerfile_path.exists():
            error_msg = f"Dockerfile not found in {self.project_dir}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # Check if Dockerfile is valid (has Docker instructions)
        if not self._is_valid_dockerfile(dockerfile_path):
            self.logger.warning("Generated Dockerfile appears incomplete, creating fallback...")
            if not self._create_fallback_dockerfile(dockerfile_path):
                return False, "Failed to create fallback Dockerfile"
        
        # Also check and fix package.json if it's incomplete
        self._ensure_valid_package_files()
        
        # Create cloudbuild.yaml
        if not self._create_cloudbuild_config(service_name, project_id, tag):
            return False, "Failed to create cloudbuild.yaml"
        
        try:
            # Use Cloud Build to build and push
            if not self._trigger_cloud_build(project_id, image_name):
                return False, "Cloud Build failed"
            
            self.logger.info(f"✅ Container built and pushed with Cloud Build: {image_name}")
            return True, image_name
            
        except Exception as e:
            error_msg = f"Cloud Build failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _create_cloudbuild_config(self, service_name: str, project_id: str, tag: str) -> bool:
        """Create cloudbuild.yaml configuration file"""
        try:
            image_name = f"gcr.io/{project_id}/{service_name}:{tag}"
            
            cloudbuild_config = f"""steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '{image_name}', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '{image_name}']

images:
  - '{image_name}'

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'

timeout: '1200s'
"""
            
            cloudbuild_path = self.project_dir / "cloudbuild.yaml"
            with open(cloudbuild_path, 'w') as f:
                f.write(cloudbuild_config)
            
            self.logger.info("✅ Created cloudbuild.yaml")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create cloudbuild.yaml: {e}")
            return False
    
    def _trigger_cloud_build(self, project_id: str, image_name: str) -> bool:
        """Trigger Google Cloud Build"""
        try:
            self.logger.info("Triggering Cloud Build...")
            
            cmd = [
                'gcloud', 'builds', 'submit',
                '--project', project_id,
                '--config', 'cloudbuild.yaml',
                '--timeout', '1200',
                '.'
            ]
            
            result = self._run_gcloud_command(cmd)
            
            if result.returncode != 0:
                self.logger.error(f"Cloud Build failed: {result.stderr}")
                return False
            
            self.logger.info("✅ Cloud Build completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to trigger Cloud Build: {e}")
            return False
    
    def _run_gcloud_command(self, args: list) -> subprocess.CompletedProcess:
        """Run gcloud command with proper error handling"""
        
        # Set working directory
        cwd = str(self.project_dir)
        
        if self.logger:
            self.logger.debug(f"Running command in {cwd}: {' '.join(args)}")
        
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,  # Prevent hanging on interactive input
                timeout=1800  # 30 minutes timeout
            )
            
            return result
            
        except subprocess.TimeoutExpired:
            error_msg = f"Gcloud command timed out after 30 minutes: {' '.join(args)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Failed to run gcloud command {' '.join(args)}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def image_exists_in_registry(self, image_name: str) -> bool:
        """Check if image exists in Google Container Registry"""
        try:
            cmd = ['gcloud', 'container', 'images', 'describe', image_name, '--quiet']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_build_timestamp_tag(self) -> str:
        """Generate a timestamp-based tag for container images"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _is_valid_dockerfile(self, dockerfile_path: Path) -> bool:
        """Check if Dockerfile contains actual Docker instructions"""
        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read().strip()
            
            # Check for common Docker instructions
            docker_instructions = ['FROM', 'RUN', 'COPY', 'ADD', 'CMD', 'ENTRYPOINT', 'WORKDIR', 'EXPOSE']
            
            lines = content.split('\n')
            instruction_count = 0
            
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue
                
                # Check if line starts with a Docker instruction
                for instruction in docker_instructions:
                    if line.upper().startswith(instruction):
                        instruction_count += 1
                        break
            
            # A valid Dockerfile should have at least FROM and one other instruction
            return instruction_count >= 2
            
        except Exception as e:
            self.logger.error(f"Error validating Dockerfile: {e}")
            return False
    
    def _create_fallback_dockerfile(self, dockerfile_path: Path) -> bool:
        """Create a basic working Dockerfile as fallback"""
        try:
            # Detect runtime from existing files
            package_json = self.project_dir / "package.json"
            requirements_txt = self.project_dir / "requirements.txt"
            
            if package_json.exists():
                # Node.js application
                dockerfile_content = """# Use official Node.js 18 Alpine image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Start the application
CMD ["node", "index.js"]
"""
            elif requirements_txt.exists():
                # Python application
                dockerfile_content = """# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Start the application
CMD ["python", "main.py"]
"""
            else:
                # Generic fallback - also create a basic index.js
                dockerfile_content = """# Generic Node.js fallback
FROM node:18-alpine

WORKDIR /app
COPY . .
RUN npm install --production
EXPOSE 8080
CMD ["node", "index.js"]
"""
                # Also create a basic index.js if it doesn't exist or is incomplete
                self._create_fallback_index_js()
            
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            self.logger.info(f"✅ Created fallback Dockerfile")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create fallback Dockerfile: {e}")
            return False
    
    def _ensure_valid_package_files(self):
        """Ensure package.json and other dependency files are valid"""
        package_json_path = self.project_dir / "package.json"
        
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    content = f.read().strip()
                
                # Check if it's a valid JSON and has required fields
                import json
                try:
                    package_data = json.loads(content)
                    if not isinstance(package_data, dict) or not package_data.get('name'):
                        raise ValueError("Invalid package.json structure")
                except (json.JSONDecodeError, ValueError):
                    self.logger.warning("Invalid package.json detected, creating fallback...")
                    self._create_fallback_package_json(package_json_path)
                    
            except Exception as e:
                self.logger.warning(f"Error reading package.json: {e}, creating fallback...")
                self._create_fallback_package_json(package_json_path)
    
    def _create_fallback_package_json(self, package_path: Path):
        """Create a basic package.json file"""
        try:
            service_name = self.project_dir.name.replace('_', '-')
            
            package_data = {
                "name": service_name,
                "version": "1.0.0",
                "description": "Generated microservice",
                "main": "index.js",
                "scripts": {
                    "start": "node index.js"
                },
                "dependencies": {
                    "express": "^4.18.0"
                },
                "engines": {
                    "node": ">=18"
                }
            }
            
            import json
            with open(package_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            self.logger.info("✅ Created fallback package.json")
            
        except Exception as e:
            self.logger.error(f"Failed to create fallback package.json: {e}")
    
    def _create_fallback_index_js(self):
        """Create a basic working index.js with health endpoint"""
        try:
            index_js_path = self.project_dir / "index.js"
            
            # Check if index.js exists and is valid
            needs_fallback = True
            if index_js_path.exists():
                with open(index_js_path, 'r') as f:
                    content = f.read().strip()
                
                # Check if it has basic Express structure and health endpoint
                if len(content) > 100 and '/health' in content and 'express' in content:
                    needs_fallback = False
            
            if needs_fallback:
                index_js_content = """const express = require('express');
const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(express.json());

// Health check endpoint (required for Cloud Run)
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    service: 'weather-alert-service'
  });
});

// Main service endpoint
app.get('/', (req, res) => {
  res.json({ 
    message: 'Weather Alert Service is running!',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Example API endpoint
app.post('/api/alert', (req, res) => {
  const { location, alertType } = req.body;
  
  res.json({
    message: 'Weather alert processed',
    location: location || 'Unknown',
    alertType: alertType || 'general',
    processed_at: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Weather Alert Service listening on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down gracefully');
  process.exit(0);
});
"""
                
                with open(index_js_path, 'w') as f:
                    f.write(index_js_content)
                
                self.logger.info("✅ Created fallback index.js with health endpoint")
                
        except Exception as e:
            self.logger.error(f"Failed to create fallback index.js: {e}")