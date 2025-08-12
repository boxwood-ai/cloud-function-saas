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

# Load environment variables
load_dotenv()


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
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.model = model or os.getenv('CLAUDE_MODEL') or self._get_latest_sonnet_model()
        self.max_tokens = int(os.getenv('CLAUDE_MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('CLAUDE_TEMPERATURE', '0.1'))
    
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
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are an expert Cloud Run developer. Generate complete, production-ready Node.js Cloud Run functions based on specifications.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            generated_code = response.content[0].text
            return self._parse_generated_files(generated_code)
            
        except Exception as e:
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

Please provide the files in this format:
```javascript
// FILE: index.js
[code here]
```

```json
// FILE: package.json
[code here]
```
"""
        return prompt
    
    def _parse_generated_files(self, generated_content: str) -> Dict[str, str]:
        """Parse AI-generated code into file dictionary"""
        files = {}
        
        # Extract code blocks with file names
        pattern = r'```(?:\w+)?\s*\n?// FILE: ([\w./]+)\n(.*?)```'
        matches = re.findall(pattern, generated_content, re.DOTALL)
        
        for filename, content in matches:
            files[filename] = content.strip()
        
        # If no structured output, create basic files
        if not files:
            files = self._fallback_generation_simple(generated_content)
        
        return files
    
    def _fallback_generation(self, spec: ServiceSpec) -> Dict[str, str]:
        """Fallback code generation without AI"""
        return {
            'index.js': self._generate_basic_index(spec),
            'package.json': self._generate_basic_package_json(spec)
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


class CloudRunDeployer:
    """Deploy generated functions to Google Cloud Run"""
    
    def __init__(self, project_id: Optional[str] = None, region: Optional[str] = None):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = region or os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
    
    def deploy(self, service_name: str, source_dir: str) -> bool:
        """Deploy to Cloud Run"""
        try:
            # Set project
            subprocess.run(['gcloud', 'config', 'set', 'project', self.project_id], 
                          check=True, capture_output=True)
            
            # Deploy to Cloud Run
            cmd = [
                'gcloud', 'run', 'deploy', service_name,
                '--source', source_dir,
                '--platform', 'managed',
                '--region', self.region,
                '--allow-unauthenticated'
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("Deployment successful!")
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Deployment failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            print(f"Deployment error: {e}")
            return False


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
        """
    )
    parser.add_argument('spec_file', help='Path to spec.md file')
    parser.add_argument('--project', help='Google Cloud project ID (overrides .env)')
    parser.add_argument('--region', help='Deployment region (overrides .env)')
    parser.add_argument('--output-dir', help='Output directory (default: temp dir)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate configuration, don\'t deploy')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
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
    
    # Generate code
    print("\n🤖 Generating Cloud Run function code with Claude...")
    code_generator = CodeGenerator()
    
    try:
        generated_files = code_generator.generate_cloud_function(spec)
        if not generated_files:
            print("❌ Error: Failed to generate code")
            sys.exit(1)
        print(f"✅ Generated {len(generated_files)} files successfully")
    except Exception as e:
        print(f"❌ Error generating code: {e}")
        sys.exit(1)
    
    # Create output directory
    output_dir = args.output_dir or tempfile.mkdtemp(prefix='cloud-function-')
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        sys.exit(1)
    
    # Write generated files
    print(f"\n📝 Writing generated files to {output_dir}...")
    try:
        for filename, content in generated_files.items():
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Created: {filename}")
            if args.verbose:
                print(f"      Size: {len(content)} characters")
    except Exception as e:
        print(f"❌ Error writing files: {e}")
        sys.exit(1)
    
    # Deploy to Cloud Run
    print(f"\n🚀 Deploying to Google Cloud Run...")
    service_name = spec.name.lower().replace(' ', '-').replace('_', '-')
    deployer = CloudRunDeployer(args.project, args.region)
    
    if not deployer.project_id:
        print("❌ Error: No Google Cloud project specified. Use --project or set GOOGLE_CLOUD_PROJECT in .env")
        sys.exit(1)
    
    print(f"   • Service name: {service_name}")
    print(f"   • Project: {deployer.project_id}")
    print(f"   • Region: {deployer.region}")
    
    try:
        success = deployer.deploy(service_name, output_dir)
        
        if success:
            print(f"\n🎉 Successfully deployed {spec.name} to Cloud Run!")
            service_url = f"https://{service_name}-{deployer.project_id}.{deployer.region}.run.app"
            print(f"🌐 Service URL: {service_url}")
            if args.verbose:
                print(f"\n💡 Next steps:")
                print(f"   • Test your API: curl {service_url}")
                print(f"   • View logs: gcloud logs read --service={service_name}")
                print(f"   • Monitor: https://console.cloud.google.com/run/detail/{deployer.region}/{service_name}/overview")
        else:
            print("\n❌ Deployment failed")
            print(f"💡 Generated files are available at: {output_dir}")
            print("💡 You can deploy manually with: gcloud run deploy --source .")
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        sys.exit(1)
    
    # Clean up temp directory if we created it
    if not args.output_dir:
        try:
            shutil.rmtree(output_dir)
            if args.verbose:
                print(f"🗑️  Cleaned up temporary directory: {output_dir}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up temp directory: {e}")


if __name__ == '__main__':
    main()