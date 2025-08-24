"""
Specification parsing components for the Cloud Function Generator
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class ServiceSpec:
    """Parsed service specification"""
    name: str
    description: str
    runtime: str
    endpoints: List[Dict[str, Any]]
    models: Dict[str, Any]
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
            'models': {},
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
                current_model = model_name
                spec_data['models'][model_name] = []
            elif current_section == 'models' and current_model and line.startswith('- '):
                field_def = line[2:]
                spec_data['models'][current_model].append(field_def)
        
        return ServiceSpec(**spec_data)