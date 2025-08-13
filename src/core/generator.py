"""
AI-powered code generation using various LLM providers.
"""
import os
import re
import json
from typing import Dict, List, Optional
import anthropic
from .parser import ServiceSpec


class CodeGenerator:
    """Generate Cloud Run function code using AI"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, debug: bool = False):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.model = model or os.getenv('CLAUDE_MODEL') or 'claude-sonnet-4-20250514'
        self.max_tokens = int(os.getenv('CLAUDE_MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('CLAUDE_TEMPERATURE', '0.1'))
        self.debug = debug
    
    def generate_cloud_function(self, spec: ServiceSpec, runtime: str = 'nodejs') -> Dict[str, str]:
        """Generate complete Cloud Run function code"""
        
        prompt = self._build_prompt(spec, runtime)
        
        if self.debug:
            print(f"🔍 Debug - Using model: {self.model}")
            print(f"🔍 Debug - Prompt length: {len(prompt)} characters")
        
        try:
            if self.debug:
                print("🔍 Debug - Sending request to Claude...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are an expert cloud developer. Generate production-ready code based on specifications.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            generated_code = response.content[0].text
            files = self._parse_generated_files(generated_code)
            
            # Always ensure we have required files
            files = self._ensure_required_files(files, spec, runtime)
            
            if self.debug:
                print(f"🔍 Debug - Generated {len(files)} files: {list(files.keys())}")
            
            return files
            
        except Exception as e:
            if self.debug:
                print(f"🔍 Debug - Error: {type(e).__name__}: {e}")
            return self._fallback_generation(spec, runtime)
    
    def _build_prompt(self, spec: ServiceSpec, runtime: str) -> str:
        """Build AI prompt from spec"""
        if runtime == 'nodejs':
            return self._build_nodejs_prompt(spec)
        elif runtime == 'python':
            return self._build_python_prompt(spec)
        else:
            raise ValueError(f"Unsupported runtime: {runtime}")
    
    def _build_nodejs_prompt(self, spec: ServiceSpec) -> str:
        """Build Node.js specific prompt"""
        prompt = f"""
Generate a complete Node.js Cloud Run service for:

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
1. Express.js with proper middleware
2. Input validation and error handling
3. Structured logging with correlationId
4. Health check endpoint
5. Graceful shutdown handling
6. Dockerfile with EXPOSE 8080
7. package.json with proper dependencies
8. Security best practices

Generate these files:
```javascript
// FILE: index.js
[code]
```

```json
// FILE: package.json
[code]
```

```dockerfile
// FILE: Dockerfile
[code]
```
"""
        return prompt
    
    def _build_python_prompt(self, spec: ServiceSpec) -> str:
        """Build Python specific prompt"""
        # TODO: Implement Python prompt generation
        raise NotImplementedError("Python runtime not yet supported")
    
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
                print(f"🔍 Debug - Extracted: {filename} ({len(content)} chars)")
        
        return files
    
    def _ensure_required_files(self, files: Dict[str, str], spec: ServiceSpec, runtime: str) -> Dict[str, str]:
        """Ensure all required files are present"""
        if runtime == 'nodejs':
            if 'package.json' not in files:
                files['package.json'] = self._generate_default_package_json(spec)
            if 'index.js' not in files:
                files['index.js'] = self._generate_default_index_js(spec)
            if 'Dockerfile' not in files:
                files['Dockerfile'] = self._generate_default_dockerfile()
        
        return files
    
    def _generate_default_package_json(self, spec: ServiceSpec) -> str:
        """Generate default package.json"""
        return json.dumps({
            "name": spec.name.lower().replace(' ', '-'),
            "version": "1.0.0",
            "description": spec.description,
            "main": "index.js",
            "scripts": {
                "start": "node index.js",
                "dev": "nodemon index.js",
                "test": "jest"
            },
            "dependencies": {
                "express": "^4.18.2",
                "cors": "^2.8.5",
                "helmet": "^7.1.0"
            },
            "devDependencies": {
                "nodemon": "^3.0.1",
                "jest": "^29.7.0"
            },
            "engines": {
                "node": ">=20"
            }
        }, indent=2)
    
    def _generate_default_index_js(self, spec: ServiceSpec) -> str:
        """Generate default Express.js application"""
        return f"""const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const app = express();

// Security middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Health check
app.get('/', (req, res) => {{
  res.json({{ 
    status: 'healthy', 
    service: '{spec.name}',
    timestamp: new Date().toISOString() 
  }});
}});

// TODO: Implement endpoints for {spec.name}
{chr(10).join([f"// {endpoint['method']} {endpoint['path']} - {endpoint['description']}" for endpoint in spec.endpoints])}

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {{
  console.log(`{spec.name} listening on port ${{PORT}}`);
}});

module.exports = app;
"""
    
    def _generate_default_dockerfile(self) -> str:
        """Generate default Dockerfile"""
        return """FROM node:20-slim

WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Install dependencies and curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \\
    && npm install --only=production && npm cache clean --force

# Copy source code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /usr/src/app
USER appuser

# REQUIRED: Expose port 8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/ || exit 1

CMD ["npm", "start"]
"""
    
    def _fallback_generation(self, spec: ServiceSpec, runtime: str) -> Dict[str, str]:
        """Fallback generation when AI fails"""
        if runtime == 'nodejs':
            return {
                'index.js': self._generate_default_index_js(spec),
                'package.json': self._generate_default_package_json(spec),
                'Dockerfile': self._generate_default_dockerfile()
            }
        else:
            raise ValueError(f"Fallback not implemented for runtime: {runtime}")