"""
Code generation components for the Cloud Function Generator
"""

import os
import re
import json
from typing import Dict, Optional
import anthropic

from spec_parser import ServiceSpec


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