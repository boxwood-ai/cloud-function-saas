#!/usr/bin/env python3
"""
Cloud Function Microservice Generator Prototype
Transforms spec.md files into deployed Google Cloud Run functions
"""

import os
import sys
import re
import json
import tempfile
import shutil
import subprocess
from typing import Dict, List, Any, Optional
import argparse
from dataclasses import dataclass
import anthropic
from dotenv import load_dotenv
from datetime import datetime
import logging
import traceback

# Load environment variables
load_dotenv()


def sanitize_secrets(text: str) -> str:
    """Remove common secrets and sensitive information from text"""
    import re
    
    # Common secret patterns to redact
    patterns = [
        # API keys and tokens
        (r'["\s=](sk-[a-zA-Z0-9]{48})', r'\1[REDACTED-API-KEY]'),
        (r'["\s=](xoxb-[a-zA-Z0-9-]{50,})', r'\1[REDACTED-SLACK-TOKEN]'),
        (r'["\s=]([A-Za-z0-9]{32,})', r'\1[REDACTED-TOKEN]'),
        # Environment variables that might contain secrets
        (r'(API_KEY[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(SECRET[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(PASSWORD[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        (r'(TOKEN[^=]*=)[^\s\n]+', r'\1[REDACTED]'),
        # JWT tokens
        (r'(eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', r'[REDACTED-JWT]'),
        # URLs with credentials
        (r'(https?://[^:]+:)[^@]+(@)', r'\1[REDACTED]\2'),
    ]
    
    sanitized = text
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized


def setup_logging(output_dir: str, debug: bool = False) -> logging.Logger:
    """Setup logging to both console and file"""
    # Create logger
    logger = logging.getLogger('cloud_function_generator')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create log file path
    log_file = os.path.join(output_dir, 'generation.log')
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # File handler - detailed logging with restricted permissions
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Set restrictive permissions on log file (600 - owner only)
    try:
        import stat
        os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)  # 600 permissions
    except Exception:
        pass  # Continue if chmod fails
    
    # Console handler - only if debug mode
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    logger.info("=" * 60)
    logger.info("Cloud Function Generator - Session Started")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Debug mode: {debug}")
    logger.info("=" * 60)
    
    return logger


@dataclass
class ServiceSpec:
    """Parsed service specification"""
    name: str
    description: str
    runtime: str
    endpoints: List[Dict[str, Any]]
    models: List[Dict[str, Any]]
    business_logic: Optional[str] = None
    database: Optional[Dict[str, Any]] = None
    deployment: Optional[Dict[str, Any]] = None


class SpecParser:
    """Parse markdown specification files"""
    
    def parse(self, spec_content: str) -> ServiceSpec:
        """Parse markdown spec into ServiceSpec object"""
        lines = spec_content.split('\n')
        spec_data = {
            'name': '',
            'description': '',
            'runtime': 'Node.js 20',
            'endpoints': [],
            'models': [],
            'business_logic': None,
            'database': None,
            'deployment': None
        }
        
        current_section = None
        current_endpoint = None
        current_model = None
        
        for line in lines:
            line = line.strip()
            
            # Parse service header
            if line.startswith('# Service Name:'):
                spec_data['name'] = line.replace('# Service Name:', '').strip()
            elif line.startswith('Description:'):
                spec_data['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Runtime:'):
                spec_data['runtime'] = line.replace('Runtime:', '').strip()
            
            # Parse sections
            elif line == '## Endpoints':
                current_section = 'endpoints'
            elif line == '## Models':
                current_section = 'models'
            elif line == '## Business Logic':
                current_section = 'business_logic'
            elif line == '## Database':
                current_section = 'database'
            elif line == '## Deployment':
                current_section = 'deployment'
            
            # Parse endpoint definitions
            elif current_section == 'endpoints' and line.startswith('### '):
                method_path = line.replace('### ', '')
                parts = method_path.split(' ', 1)
                current_endpoint = {
                    'method': parts[0] if len(parts) > 0 else 'GET',
                    'path': parts[1] if len(parts) > 1 else '/',
                    'description': '',
                    'input': None,
                    'output': None,
                    'auth': 'None'
                }
                spec_data['endpoints'].append(current_endpoint)
            elif current_section == 'endpoints' and current_endpoint and line.startswith('- '):
                field_value = line[2:]
                if field_value.startswith('Description:'):
                    current_endpoint['description'] = field_value.replace('Description:', '').strip()
                elif field_value.startswith('Input:'):
                    current_endpoint['input'] = field_value.replace('Input:', '').strip()
                elif field_value.startswith('Output:'):
                    current_endpoint['output'] = field_value.replace('Output:', '').strip()
                elif field_value.startswith('Auth:'):
                    current_endpoint['auth'] = field_value.replace('Auth:', '').strip()
            
            # Parse model definitions
            elif current_section == 'models' and line.startswith('### '):
                model_name = line.replace('### ', '')
                current_model = {
                    'name': model_name,
                    'fields': []
                }
                spec_data['models'].append(current_model)
            elif current_section == 'models' and current_model and line.startswith('- '):
                field_def = line[2:]
                current_model['fields'].append(field_def)
        
        return ServiceSpec(**spec_data)


class CodeGenerator:
    """Generate Cloud Run function code using Claude"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, debug: bool = False):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.model = model or os.getenv('CLAUDE_MODEL') or self._get_latest_sonnet_model()
        self.max_tokens = int(os.getenv('CLAUDE_MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('CLAUDE_TEMPERATURE', '0.1'))
        self.debug = debug
    
    def _get_latest_sonnet_model(self) -> str:
        """Query Anthropic API to get the latest Claude Sonnet model"""
        try:
            # Get available models from Anthropic API
            # Note: This assumes there's a models endpoint. If not available,
            # we'll use a reasonable default and known model patterns
            
            # Known Sonnet models in order of release (most recent first)
            known_models = [
                "claude-sonnet-4-20250514",    # Sonnet 4 (latest)
                "claude-3-5-sonnet-20241022",  # Sonnet 3.5
                "claude-3-5-sonnet-20240620", 
                "claude-3-sonnet-20240229"
            ]
            
            # Try each model to see which one is available
            for model in known_models:
                try:
                    # Test with a minimal request to see if model is available
                    test_response = self.client.messages.create(
                        model=model,
                        max_tokens=1,
                        messages=[{"role": "user", "content": "test"}]
                    )
                    print(f"Using latest available Sonnet model: {model}")
                    return model
                except Exception:
                    continue
            
            # Fallback to a known working model
            fallback_model = "claude-sonnet-4-20250514"
            print(f"Using fallback Sonnet model: {fallback_model}")
            return fallback_model
            
        except Exception as e:
            print(f"Error detecting latest model, using fallback: {e}")
            return "claude-sonnet-4-20250514"
    
    def generate_cloud_function(self, spec: ServiceSpec) -> Dict[str, str]:
        """Generate complete Cloud Run function code"""
        
        # Create the prompt for AI code generation
        prompt = self._build_prompt(spec)
        
        if self.debug:
            print(f"\n🔍 Debug - Using model: {self.model}")
            print(f"🔍 Debug - Max tokens: {self.max_tokens}")
            print(f"🔍 Debug - Temperature: {self.temperature}")
            print(f"🔍 Debug - Prompt length: {len(prompt)} characters")
            print(f"🔍 Debug - Prompt preview: {prompt[:200]}...")
        
        try:
            if self.debug:
                print("🔍 Debug - Sending request to Claude...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are an expert Cloud Run developer. Generate complete, production-ready Node.js Cloud Run functions based on specifications.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if self.debug:
                print(f"🔍 Debug - Response received, length: {len(response.content[0].text)} characters")
                print(f"🔍 Debug - Response preview: {response.content[0].text[:200]}...")
            
            generated_code = response.content[0].text
            files = self._parse_generated_files(generated_code)
            
            if self.debug:
                print(f"🔍 Debug - Parsed {len(files)} files: {list(files.keys())}")
            
            return files
            
        except Exception as e:
            if self.debug:
                print(f"🔍 Debug - Error occurred: {type(e).__name__}: {e}")
            print(f"Error generating code: {e}")
            return self._fallback_generation(spec)
    
    def _build_prompt(self, spec: ServiceSpec) -> str:
        """Build AI prompt from spec"""
        prompt = f"""
Generate a complete Google Cloud Run function for the following specification:

Service Name: {spec.name}
Description: {spec.description}
Runtime: {spec.runtime}

Endpoints:
"""
        for endpoint in spec.endpoints:
            prompt += f"- {endpoint['method']} {endpoint['path']}: {endpoint['description']}\n"
            if endpoint['input']:
                prompt += f"  Input: {endpoint['input']}\n"
            if endpoint['output']:
                prompt += f"  Output: {endpoint['output']}\n"
        
        prompt += "\nData Models:\n"
        for model in spec.models:
            prompt += f"- {model['name']}:\n"
            for field in model['fields']:
                prompt += f"  - {field}\n"
        
        prompt += """

Requirements:
1. Generate a main index.js file that exports a Cloud Run HTTP function
2. Include proper error handling and input validation
3. Use express.js for routing
4. Include package.json with all dependencies
5. Follow Google Cloud Run best practices
6. Include basic logging with console.log
7. MUST include a Dockerfile with these requirements:
   - FROM node:20-slim (or compatible)
   - EXPOSE 8080 (REQUIRED for Cloud Run)
   - Install curl for health checks
   - Use non-root user for security
   - Set PORT environment variable handling
   - CMD ["npm", "start"]

Please provide the files in this format:
```javascript
// FILE: index.js
[code here]
```

```json
// FILE: package.json
[code here]
```

```dockerfile
// FILE: Dockerfile
[code here]
```
"""
        return prompt
    
    def _parse_generated_files(self, generated_content: str) -> Dict[str, str]:
        """Parse AI-generated code into file dictionary"""
        files = {}
        
        if self.debug:
            print("🔍 Debug - Parsing generated files...")
        
        # Extract code blocks with file names
        pattern = r'```(?:\w+)?\s*\n?// FILE: ([\w./]+)\n(.*?)```'
        matches = re.findall(pattern, generated_content, re.DOTALL)
        
        if self.debug:
            print(f"🔍 Debug - Found {len(matches)} file matches")
        
        for filename, content in matches:
            files[filename] = content.strip()
            if self.debug:
                print(f"🔍 Debug - Extracted file: {filename} ({len(content)} chars)")
        
        # If no structured output, create basic files
        if not files:
            if self.debug:
                print("🔍 Debug - No structured files found, using fallback parsing")
            files = self._fallback_generation_simple(generated_content)
        
        # Always ensure we have a Dockerfile - add it if missing
        if 'Dockerfile' not in files:
            if self.debug:
                print("🔍 Debug - Adding missing Dockerfile")
            files['Dockerfile'] = self._generate_basic_dockerfile_simple()
        
        return files
    
    def _fallback_generation(self, spec: ServiceSpec) -> Dict[str, str]:
        """Fallback code generation without AI"""
        return {
            'index.js': self._generate_basic_index(spec),
            'package.json': self._generate_basic_package_json(spec),
            'Dockerfile': self._generate_basic_dockerfile(spec)
        }
    
    def _fallback_generation_simple(self, content: str) -> Dict[str, str]:
        """Simple fallback when AI output isn't structured"""
        # Try to extract JavaScript code
        js_pattern = r'```(?:javascript|js)?\s*\n(.*?)```'
        js_matches = re.findall(js_pattern, content, re.DOTALL)
        
        json_pattern = r'```json\s*\n(.*?)```'
        json_matches = re.findall(json_pattern, content, re.DOTALL)
        
        files = {}
        if js_matches:
            files['index.js'] = js_matches[0].strip()
        if json_matches:
            files['package.json'] = json_matches[0].strip()
        
        # Always ensure we have a Dockerfile
        if 'Dockerfile' not in files:
            files['Dockerfile'] = self._generate_basic_dockerfile_simple()
        
        return files
    
    def _generate_basic_index(self, spec: ServiceSpec) -> str:
        """Generate basic index.js template"""
        routes = []
        for endpoint in spec.endpoints:
            method = endpoint['method'].lower()
            path = endpoint['path']
            handler_name = f"handle{endpoint['method']}{path.replace('/', '_').replace(':', '_')}"
            routes.append(f'app.{method}("{path}", {handler_name});')
        
        return f"""const express = require('express');
const app = express();

app.use(express.json());

// Health check endpoint
app.get('/', (req, res) => {{
  res.json({{ status: 'ok', service: '{spec.name}' }});
}});

{chr(10).join(routes)}

// Error handler
app.use((err, req, res, next) => {{
  console.error('Error:', err);
  res.status(500).json({{ error: 'Internal server error' }});
}});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {{
  console.log(`{spec.name} listening on port ${{PORT}}`);
}});

module.exports = app;
"""
    
    def _generate_basic_package_json(self, spec: ServiceSpec) -> str:
        """Generate basic package.json"""
        return json.dumps({
            "name": spec.name.lower().replace(' ', '-'),
            "version": "1.0.0",
            "description": spec.description,
            "main": "index.js",
            "scripts": {
                "start": "node index.js",
                "dev": "nodemon index.js"
            },
            "dependencies": {
                "express": "^4.18.2"
            },
            "engines": {
                "node": ">=18"
            }
        }, indent=2)
    
    def _generate_basic_dockerfile(self, spec: ServiceSpec) -> str:
        """Generate basic Dockerfile with all Cloud Run requirements"""
        return f"""FROM node:20-slim

# Set working directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Install dependencies and curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \\
    && npm install --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /usr/src/app
USER appuser

# REQUIRED: Expose port 8080 for Cloud Run
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/ || exit 1

# Start the application
CMD ["npm", "start"]
"""

    def _generate_basic_dockerfile_simple(self) -> str:
        """Generate basic Dockerfile without spec dependency"""
        return """FROM node:20-slim

# Set working directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Install dependencies and curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \\
    && npm install --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /usr/src/app
USER appuser

# REQUIRED: Expose port 8080 for Cloud Run
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/ || exit 1

# Start the application
CMD ["npm", "start"]
"""


class CloudRunDeployer:
    """Deploy generated functions to Google Cloud Run"""
    
    def __init__(self, project_id: Optional[str] = None, region: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = region or os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        self.logger = logger or logging.getLogger('cloud_function_generator')
        
        self.logger.info(f"CloudRunDeployer initialized with project_id='{self.project_id}', region='{self.region}'")
        
        # Validate region format (should not include zone suffix like -a, -b, -c)
        if self.region and self.region.endswith(('-a', '-b', '-c', '-d', '-e', '-f')):
            warning_msg = f"Region '{self.region}' looks like a zone. Removing zone suffix for Cloud Run."
            print(f"⚠️  Warning: {warning_msg}")
            self.logger.warning(warning_msg)
            self.region = self.region[:-2]  # Remove zone suffix
            self.logger.info(f"Region corrected to: {self.region}")
    
    def deploy(self, service_name: str, source_dir: str) -> bool:
        """Deploy to Cloud Run"""
        self.logger.info("=" * 40)
        self.logger.info("STARTING CLOUD RUN DEPLOYMENT")
        self.logger.info("=" * 40)
        self.logger.info(f"Service name: {service_name}")
        self.logger.info(f"Project: {self.project_id}")
        self.logger.info(f"Region: {self.region}")
        self.logger.info(f"Source directory: {source_dir}")
        
        print(f"\n📋 Starting Cloud Run deployment...")
        print(f"   • Service name: {service_name}")
        print(f"   • Project: {self.project_id}")
        print(f"   • Region: {self.region}")
        print(f"   • Source directory: {source_dir}")
        
        try:
            # Set project
            self.logger.info("Setting gcloud project...")
            print("\n🔧 Setting gcloud project...")
            set_project_cmd = ['gcloud', 'config', 'set', 'project', self.project_id]
            self.logger.debug(f"Running command: {' '.join(set_project_cmd)}")
            print(f"   Running: {' '.join(set_project_cmd)}")
            
            result = subprocess.run(set_project_cmd, check=True, capture_output=True, text=True)
            self.logger.debug(f"Set project result - stdout: {result.stdout}, stderr: {result.stderr}, returncode: {result.returncode}")
            
            if result.stdout.strip():
                success_msg = f"Project set: {result.stdout.strip()}"
                print(f"   ✅ {success_msg}")
                self.logger.info(success_msg)
            
            # Deploy to Cloud Run
            self.logger.info("Starting Cloud Run deployment...")
            print("\n🚀 Deploying to Cloud Run...")
            cmd = [
                'gcloud', 'run', 'deploy', service_name,
                '--source', source_dir,
                '--platform', 'managed',
                '--region', self.region,
                '--allow-unauthenticated'
            ]
            self.logger.info(f"Running deployment command: {' '.join(cmd)}")
            print(f"   Running: {' '.join(cmd)}")
            print("   This may take a few minutes...")
            
            # Run deployment with real-time logging
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, universal_newlines=True)
            
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    self.logger.debug(f"Deploy output: {line}")
            
            return_code = process.poll()
            full_output = '\n'.join(output_lines)
            
            # Ensure we have a valid return code
            if return_code is None:
                return_code = process.wait()  # Wait for the process to finish
            
            self.logger.debug(f"Process completed with return code: {return_code}")
            
            if return_code == 0:
                print("\n🎉 Deployment successful!")
                print(full_output)
                self.logger.info("Deployment completed successfully")
                self.logger.debug(f"Full deployment output:\n{full_output}")
                return True
            else:
                raise subprocess.CalledProcessError(return_code, cmd, full_output)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Deployment failed with exit code {e.returncode}"
            print(f"\n❌ {error_msg}")
            print(f"Command that failed: {' '.join(e.cmd)}")
            self.logger.error(error_msg)
            self.logger.error(f"Failed command: {' '.join(e.cmd)}")
            
            if e.output:
                sanitized_output = sanitize_secrets(str(e.output))
                print(f"Command output: {sanitized_output}")
                self.logger.error(f"Command output:\n{sanitized_output}")
            if hasattr(e, 'stdout') and e.stdout:
                sanitized_stdout = sanitize_secrets(str(e.stdout))
                print(f"Standard output: {sanitized_stdout}")
                self.logger.error(f"Standard output:\n{sanitized_stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                sanitized_stderr = sanitize_secrets(str(e.stderr))
                print(f"Error output: {sanitized_stderr}")
                self.logger.error(f"Error output:\n{sanitized_stderr}")
            
            self.logger.error(f"Full exception details: {traceback.format_exc()}")
            
            # Show debugging help
            print(f"\n🔍 For detailed build logs and debugging:")
            print(f"   • Visit: https://console.cloud.google.com/cloud-build/builds?project={self.project_id}")
            print(f"   • Look for the most recent failed build")
            print(f"   • Check build steps for specific error details")
            
            # Try to fetch build logs for more details
            self._fetch_build_logs(service_name)
            return False
        except FileNotFoundError:
            error_msg = "gcloud command not found!"
            print(f"\n❌ Error: {error_msg}")
            print("💡 Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
            self.logger.error(error_msg)
            self.logger.error("Google Cloud SDK not installed or not in PATH")
            return False
        except Exception as e:
            error_msg = f"Unexpected deployment error: {e}"
            print(f"\n❌ {error_msg}")
            self.logger.error(error_msg)
            self.logger.error(f"Full exception details: {traceback.format_exc()}")
            return False
    
    def _fetch_build_logs(self, service_name: str):
        """Fetch and display recent build logs to help debug deployment failures"""
        self.logger.info("Attempting to fetch build logs for debugging...")
        try:
            print("\n📜 Fetching recent build logs for debugging...")
            
            # Get recent Cloud Build logs (get the 3 most recent builds)
            cmd = [
                'gcloud', 'builds', 'list',
                '--limit', '3',
                '--format', 'value(id)',
                '--project', self.project_id,
                '--sort-by', '~createTime'
            ]
            self.logger.debug(f"Running build list command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.logger.debug(f"Build list result - returncode: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                build_ids = result.stdout.strip().split('\n')
                print(f"   Found recent builds: {len(build_ids)}")
                self.logger.info(f"Found {len(build_ids)} recent builds: {build_ids}")
                
                # Get logs for the most recent build
                for build_id in build_ids:
                    if build_id.strip():
                        print(f"   Fetching logs for build: {build_id}")
                        self.logger.info(f"Fetching logs for build: {build_id}")
                        
                        # Get the build logs
                        log_cmd = [
                            'gcloud', 'builds', 'log', build_id.strip(),
                            '--project', self.project_id
                        ]
                        self.logger.debug(f"Running build log command: {' '.join(log_cmd)}")
                        
                        log_result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=60)
                        self.logger.debug(f"Build log result - returncode: {log_result.returncode}")
                        
                        if log_result.returncode == 0 and log_result.stdout:
                            sanitized_log = sanitize_secrets(log_result.stdout)
                            print(f"\n🔍 Build Log Details for {build_id}:")
                            print("=" * 60)
                            # Show last 50 lines of build log (sanitized)
                            lines = sanitized_log.strip().split('\n')
                            for line in lines[-50:]:
                                print(f"   {line}")
                            print("=" * 60)
                            
                            # Log the full build log (sanitized)
                            self.logger.error(f"FULL BUILD LOG FOR {build_id}:")
                            self.logger.error("=" * 40)
                            self.logger.error(sanitized_log)
                            self.logger.error("=" * 40)
                            break  # Only show the first successful log
                        else:
                            print(f"   Could not retrieve logs for build {build_id}")
                            self.logger.warning(f"Could not retrieve logs for build {build_id}")
            else:
                print("   No recent builds found")
                self.logger.warning("No recent builds found")
                
        except subprocess.TimeoutExpired:
            timeout_msg = "Timeout while fetching build logs"
            print(f"   {timeout_msg}")
            self.logger.error(timeout_msg)
        except Exception as e:
            error_msg = f"Could not fetch build logs: {e}"
            print(f"   {error_msg}")
            self.logger.error(error_msg)
            self.logger.error(f"Build log fetch exception: {traceback.format_exc()}")
    
    def _fetch_recent_build_logs(self):
        """Fetch most recent build logs as fallback"""
        try:
            print("   Checking most recent builds...")
            
            cmd = [
                'gcloud', 'builds', 'list',
                '--limit', '1',
                '--format', 'value(id)',
                '--project', self.project_id
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                build_id = result.stdout.strip()
                print(f"   Most recent build: {build_id}")
                
                # Get the build logs
                log_cmd = [
                    'gcloud', 'builds', 'log', build_id,
                    '--project', self.project_id
                ]
                
                log_result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=60)
                
                if log_result.returncode == 0 and log_result.stdout:
                    print("\n🔍 Most Recent Build Log (last 30 lines):")
                    print("=" * 60)
                    lines = log_result.stdout.strip().split('\n')
                    for line in lines[-30:]:
                        print(f"   {line}")
                    print("=" * 60)
            
        except Exception as e:
            print(f"   Could not fetch recent build logs: {e}")


def validate_configuration():
    """Validate required configuration and environment setup"""
    errors = []
    warnings = []
    
    # Check for required environment variables
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        errors.append("ANTHROPIC_API_KEY is required. Set it in .env or environment variables.")
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        warnings.append("GOOGLE_CLOUD_PROJECT not set in .env. You'll need to specify --project flag.")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        warnings.append(".env file not found. Using environment variables and defaults.")
    
    # Check if gcloud CLI is available
    try:
        subprocess.run(['gcloud', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        errors.append("Google Cloud SDK (gcloud) is not installed or not in PATH. Please install it first.")
    
    # Check if gcloud is authenticated
    try:
        result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE'], 
                              capture_output=True, text=True, check=True)
        if 'ACTIVE' not in result.stdout:
            errors.append("No active Google Cloud authentication found. Run 'gcloud auth login' first.")
    except subprocess.CalledProcessError:
        errors.append("Unable to check Google Cloud authentication status.")
    
    # Test Anthropic API connection if key is available
    if api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            # Test with minimal request
            client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
        except anthropic.AuthenticationError:
            errors.append("Invalid ANTHROPIC_API_KEY. Please check your API key.")
        except anthropic.PermissionDeniedError:
            errors.append("Anthropic API key doesn't have permission to use Claude models.")
        except Exception as e:
            warnings.append(f"Unable to verify Anthropic API connection: {str(e)}")
    
    return errors, warnings


def main():
    """Main prototype function"""
    parser = argparse.ArgumentParser(
        description='Cloud Function Microservice Generator Prototype',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python prototype.py spec.md                    # Use .env configuration
  python prototype.py spec.md --project my-gcp   # Override GCP project
  python prototype.py spec.md --validate-only    # Only validate configuration
  python prototype.py spec.md --debug            # Enable debug output
        """
    )
    parser.add_argument('spec_file', help='Path to spec.md file')
    parser.add_argument('--project', help='Google Cloud project ID (overrides .env)')
    parser.add_argument('--region', help='Deployment region (overrides .env)')
    parser.add_argument('--output-dir', help='Output directory (default: generated/timestamp-service)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate configuration, don\'t deploy')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output to see what\'s happening')
    
    args = parser.parse_args()
    
    # Validate configuration first
    print("🔍 Validating configuration...")
    errors, warnings = validate_configuration()
    
    # Show warnings
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   • {warning}")
    
    # Show errors and exit if any
    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"   • {error}")
        print("\n💡 Please fix the above errors and try again.")
        sys.exit(1)
    
    print("✅ Configuration validated successfully!")
    
    # Exit if only validating
    if args.validate_only:
        print("\n🎉 All checks passed! Ready to generate and deploy microservices.")
        return
    
    # Check if spec file exists
    if not os.path.exists(args.spec_file):
        print(f"\n❌ Error: Spec file '{args.spec_file}' not found")
        print("💡 Make sure the file path is correct or create the spec file first.")
        sys.exit(1)
    
    # Validate spec file is readable
    try:
        with open(args.spec_file, 'r') as f:
            spec_content = f.read()
        if not spec_content.strip():
            print(f"\n❌ Error: Spec file '{args.spec_file}' is empty")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error reading spec file: {e}")
        sys.exit(1)
    
    # Read and parse spec
    print(f"\n📖 Reading spec from {args.spec_file}...")
    
    spec_parser = SpecParser()
    try:
        spec = spec_parser.parse(spec_content)
        if not spec.name:
            print("⚠️  Warning: No service name found in spec")
        if not spec.endpoints:
            print("⚠️  Warning: No endpoints defined in spec")
        print(f"✅ Parsed spec for service: {spec.name or 'Unnamed Service'}")
        if args.verbose:
            print(f"   • Description: {spec.description}")
            print(f"   • Runtime: {spec.runtime}")
            print(f"   • Endpoints: {len(spec.endpoints)}")
            print(f"   • Models: {len(spec.models)}")
    except Exception as e:
        print(f"\n❌ Error parsing spec file: {e}")
        sys.exit(1)
    
    # Generate code (before creating output directory to avoid empty log files)
    print("\n🤖 Generating Cloud Run function code with Claude...")
    code_generator = CodeGenerator(debug=args.debug)
    
    try:
        generated_files = code_generator.generate_cloud_function(spec)
        if not generated_files:
            print("❌ Error: Failed to generate code")
            sys.exit(1)
        print(f"✅ Generated {len(generated_files)} files successfully")
    except Exception as e:
        print(f"❌ Error generating code: {e}")
        sys.exit(1)
    
    # Create organized output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Create timestamped directory in generated folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        service_name_clean = (spec.name or 'unnamed').lower().replace(' ', '-').replace('_', '-')
        output_dir = os.path.join('generated', f'{timestamp}_{service_name_clean}')
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        if args.debug:
            print(f"🔍 Debug - Created output directory: {output_dir}")
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        sys.exit(1)
    
    # Setup logging now that we have the output directory
    logger = setup_logging(output_dir, args.debug)
    logger.info("Main execution started")
    logger.info(f"Arguments: spec_file={args.spec_file}, project={args.project}, region={args.region}, output_dir={args.output_dir}, debug={args.debug}")
    logger.info(f"Output directory: {output_dir}")
    
    # Write generated files
    logger.info("Writing generated files...")
    print(f"\n📝 Writing generated files to {output_dir}...")
    try:
        file_count = 0
        total_size = 0
        
        for filename, content in generated_files.items():
            file_path = os.path.join(output_dir, filename)
            logger.debug(f"Writing file: {filename} ({len(content)} bytes)")
            with open(file_path, 'w') as f:
                f.write(content)
            
            file_size = len(content)
            total_size += file_size
            file_count += 1
            
            print(f"   ✅ Created: {filename} ({file_size} bytes)")
            logger.info(f"Created file: {filename} ({file_size} bytes)")
            
            if args.verbose:
                # Show first few lines of each file for verification
                preview_lines = content.split('\n')[:3]
                preview = f"{preview_lines[0][:60]}{'...' if len(preview_lines[0]) > 60 else ''}"
                print(f"      Preview: {preview}")
                logger.debug(f"File {filename} preview: {preview}")
        
        print(f"\n📊 File generation summary:")
        print(f"   • Files created: {file_count}")
        print(f"   • Total size: {total_size} bytes")
        print(f"   • Output directory: {output_dir}")
        
        logger.info(f"File generation complete - {file_count} files, {total_size} bytes total")
        
    except Exception as e:
        error_msg = f"Error writing files: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        logger.error(f"File writing exception: {traceback.format_exc()}")
        if args.debug:
            print(f"🔍 Debug - Full traceback: {traceback.format_exc()}")
        sys.exit(1)
    
    # Deploy to Cloud Run
    print("\n🚀 Preparing for Google Cloud Run deployment...")
    service_name = spec.name.lower().replace(' ', '-').replace('_', '-')
    logger.info(f"Preparing deployment for service: {service_name}")
    deployer = CloudRunDeployer(args.project, args.region, logger)
    
    if not deployer.project_id:
        error_msg = "No Google Cloud project specified. Use --project or set GOOGLE_CLOUD_PROJECT in .env"
        print(f"❌ Error: {error_msg}")
        logger.error(error_msg)
        sys.exit(1)
    
    # Validate generated files before deployment
    print("\n🔍 Validating generated files before deployment...")
    logger.info("Validating generated files before deployment...")
    required_files = ['package.json', 'index.js', 'Dockerfile']
    missing_files = []
    validation_errors = []
    
    for file in required_files:
        file_path = os.path.join(output_dir, file)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {file} ({file_size} bytes)")
            
            # Validate file contents
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if file == 'package.json':
                    # Validate JSON and check for required fields
                    try:
                        package_data = json.loads(content)
                        
                        # Check required fields
                        if 'main' not in package_data:
                            validation_errors.append(f"{file}: Missing 'main' field")
                        elif package_data['main'] != 'index.js':
                            validation_errors.append(f"{file}: 'main' should be 'index.js', got '{package_data['main']}'")
                        
                        if 'scripts' not in package_data or 'start' not in package_data.get('scripts', {}):
                            validation_errors.append(f"{file}: Missing 'start' script")
                        
                        if 'dependencies' not in package_data:
                            validation_errors.append(f"{file}: Missing 'dependencies' section")
                        elif 'express' not in package_data['dependencies']:
                            validation_errors.append(f"{file}: Missing 'express' dependency")
                        
                        print(f"      ✅ Valid JSON with required fields")
                        
                    except json.JSONDecodeError as e:
                        validation_errors.append(f"{file}: Invalid JSON - {e}")
                        print(f"      ❌ Invalid JSON")
                
                elif file == 'index.js':
                    # Check for basic Node.js/Express patterns
                    if 'express' not in content:
                        validation_errors.append(f"{file}: Missing Express.js import")
                    if 'app.listen' not in content and 'listen(' not in content:
                        validation_errors.append(f"{file}: Missing server listen call")
                    if 'process.env.PORT' not in content:
                        validation_errors.append(f"{file}: Missing PORT environment variable usage")
                    
                    if not validation_errors or not any(file in error for error in validation_errors):
                        print(f"      ✅ Contains Express.js server code")
                
                elif file == 'Dockerfile':
                    # Check for critical Docker/Cloud Run requirements
                    dockerfile_checks = [
                        ('EXPOSE 8080', 'Missing EXPOSE 8080 directive (required for Cloud Run)'),
                        ('FROM node:', 'Missing Node.js base image'),
                        ('CMD ', 'Missing CMD directive'),
                        ('WORKDIR ', 'Missing WORKDIR directive'),
                    ]
                    
                    dockerfile_errors = []
                    for check, error_msg in dockerfile_checks:
                        if check not in content:
                            dockerfile_errors.append(f"{file}: {error_msg}")
                            validation_errors.append(f"{file}: {error_msg}")
                    
                    if not dockerfile_errors:
                        print(f"      ✅ Contains required Cloud Run directives")
                    else:
                        print(f"      ❌ Missing critical directives: {len(dockerfile_errors)}")
                        for error in dockerfile_errors:
                            print(f"        • {error.split(': ', 1)[1]}")
                
            except Exception as e:
                validation_errors.append(f"{file}: Could not validate content - {e}")
                print(f"      ⚠️ Could not validate content")
        else:
            missing_files.append(file)
            print(f"   ❌ {file} - MISSING")
    
    # Show validation results
    if missing_files:
        print(f"\n❌ Cannot deploy: Missing required files: {', '.join(missing_files)}")
        sys.exit(1)
    
    if validation_errors:
        print(f"\n⚠️ Validation warnings found:")
        for error in validation_errors:
            print(f"   • {error}")
        print(f"\n💡 These issues might cause build failures. Continuing with deployment...")
    else:
        print(f"\n✅ All files validated successfully!")
    
    print("\n📋 Deployment configuration:")
    print(f"   • Service name: {service_name}")
    print(f"   • Project ID: {deployer.project_id}")
    print(f"   • Region: {deployer.region}")
    print(f"   • Source directory: {output_dir}")
    
    try:
        logger.info("Starting deployment process...")
        success = deployer.deploy(service_name, output_dir)
        
        if success:
            success_msg = f"Successfully deployed {spec.name} to Cloud Run!"
            print(f"\n🎉 {success_msg}")
            logger.info(success_msg)
            
            service_url = f"https://{service_name}-{deployer.project_id}.{deployer.region}.run.app"
            print(f"\n🌐 Service URL: {service_url}")
            print(f"\n📊 Deployment Summary:")
            print(f"   • Service: {service_name}")
            print(f"   • URL: {service_url}")
            print(f"   • Region: {deployer.region}")
            print(f"   • Project: {deployer.project_id}")
            
            logger.info(f"Deployment successful - Service URL: {service_url}")
            logger.info(f"Final deployment summary - Service: {service_name}, Region: {deployer.region}, Project: {deployer.project_id}")
            
            if args.verbose:
                print("\n💡 Next steps:")
                print(f"   • Test health check: curl {service_url}")
                print(f"   • View logs: gcloud logs read --service={service_name} --project={deployer.project_id}")
                print(f"   • Monitor service: https://console.cloud.google.com/run/detail/{deployer.region}/{service_name}/overview?project={deployer.project_id}")
                print(f"   • Update service: gcloud run deploy {service_name} --source {output_dir} --region {deployer.region}")
        else:
            failure_msg = "Deployment failed"
            print(f"\n❌ {failure_msg}")
            print(f"💡 Generated files are available at: {output_dir}")
            print(f"💡 You can deploy manually with: gcloud run deploy {service_name} --source {output_dir} --region {deployer.region}")
            logger.error(failure_msg)
            logger.info(f"Manual deployment command: gcloud run deploy {service_name} --source {output_dir} --region {deployer.region}")
    except Exception as e:
        error_msg = f"Deployment error: {e}"
        print(f"❌ {error_msg}")
        print(f"💡 Generated files are available at: {output_dir}")
        logger.error(error_msg)
        logger.error(f"Deployment exception: {traceback.format_exc()}")
        sys.exit(1)
    
    # Keep generated files (cleanup disabled)
    print(f"📁 Generated files preserved at: {output_dir}")
    logger.info("Session completed successfully")
    logger.info("=" * 60)
    print(f"📝 Debug log saved at: {os.path.join(output_dir, 'generation.log')}")


if __name__ == '__main__':
    main()