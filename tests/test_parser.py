"""
Tests for the specification parser module.
"""
import pytest
from src.core.parser import SpecParser, ServiceSpec


class TestSpecParser:
    """Test cases for SpecParser class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = SpecParser()
    
    def test_parse_basic_spec(self):
        """Test parsing a basic service specification"""
        spec_content = """
# Service Name: Test API
Description: A test API service
Runtime: Node.js 20

## Endpoints

### GET /health
- Description: Health check endpoint
- Output: Health status object

### POST /users
- Description: Create a new user
- Input: { name: string, email: string }
- Output: Created user object

## Models

### User
- id: string (UUID)
- name: string
- email: string
"""
        
        spec = self.parser.parse(spec_content)
        
        assert spec.name == "Test API"
        assert spec.description == "A test API service"
        assert spec.runtime == "Node.js 20"
        assert len(spec.endpoints) == 2
        assert len(spec.models) == 1
    
    def test_parse_endpoints(self):
        """Test parsing endpoint definitions"""
        spec_content = """
# Service Name: API
Description: Test
Runtime: Node.js 20

## Endpoints

### GET /users
- Description: Get all users
- Output: Array of users
- Auth: Bearer token

### POST /users/:id
- Description: Update user
- Input: User data
- Output: Updated user
"""
        
        spec = self.parser.parse(spec_content)
        
        assert len(spec.endpoints) == 2
        
        # First endpoint
        endpoint1 = spec.endpoints[0]
        assert endpoint1['method'] == 'GET'
        assert endpoint1['path'] == '/users'
        assert endpoint1['description'] == 'Get all users'
        assert endpoint1['output'] == 'Array of users'
        assert endpoint1['auth'] == 'Bearer token'
        
        # Second endpoint
        endpoint2 = spec.endpoints[1]
        assert endpoint2['method'] == 'POST'
        assert endpoint2['path'] == '/users/:id'
        assert endpoint2['description'] == 'Update user'
        assert endpoint2['input'] == 'User data'
        assert endpoint2['output'] == 'Updated user'
    
    def test_parse_models(self):
        """Test parsing model definitions"""
        spec_content = """
# Service Name: API
Description: Test
Runtime: Node.js 20

## Models

### User
- id: string (UUID)
- name: string (required)
- email: string (unique)
- createdAt: timestamp

### Product
- id: number
- title: string
- price: decimal
"""
        
        spec = self.parser.parse(spec_content)
        
        assert len(spec.models) == 2
        
        # User model
        user_model = spec.models[0]
        assert user_model['name'] == 'User'
        assert len(user_model['fields']) == 4
        assert 'id: string (UUID)' in user_model['fields']
        assert 'name: string (required)' in user_model['fields']
        
        # Product model
        product_model = spec.models[1]
        assert product_model['name'] == 'Product'
        assert len(product_model['fields']) == 3
        assert 'price: decimal' in product_model['fields']
    
    def test_validate_spec_valid(self):
        """Test validation of a valid specification"""
        spec = ServiceSpec(
            name="Test API",
            description="A test service",
            runtime="Node.js 20",
            endpoints=[
                {
                    'method': 'GET',
                    'path': '/health',
                    'description': 'Health check'
                }
            ],
            models=[]
        )
        
        errors = self.parser.validate_spec(spec)
        assert len(errors) == 0
    
    def test_validate_spec_missing_name(self):
        """Test validation fails when service name is missing"""
        spec = ServiceSpec(
            name="",
            description="A test service",
            runtime="Node.js 20",
            endpoints=[
                {
                    'method': 'GET',
                    'path': '/health',
                    'description': 'Health check'
                }
            ],
            models=[]
        )
        
        errors = self.parser.validate_spec(spec)
        assert len(errors) == 1
        assert "Service name is required" in errors[0]
    
    def test_validate_spec_no_endpoints(self):
        """Test validation fails when no endpoints are defined"""
        spec = ServiceSpec(
            name="Test API",
            description="A test service",
            runtime="Node.js 20",
            endpoints=[],
            models=[]
        )
        
        errors = self.parser.validate_spec(spec)
        assert len(errors) == 1
        assert "At least one endpoint must be defined" in errors[0]
    
    def test_validate_spec_invalid_endpoint(self):
        """Test validation fails for invalid endpoint definitions"""
        spec = ServiceSpec(
            name="Test API",
            description="A test service",
            runtime="Node.js 20",
            endpoints=[
                {
                    'method': '',
                    'path': '',
                    'description': 'Invalid endpoint'
                }
            ],
            models=[]
        )
        
        errors = self.parser.validate_spec(spec)
        assert len(errors) == 2
        assert any("Path is required" in error for error in errors)
        assert any("HTTP method is required" in error for error in errors)
    
    def test_parse_empty_spec(self):
        """Test parsing an empty specification"""
        spec_content = ""
        
        spec = self.parser.parse(spec_content)
        
        assert spec.name == ""
        assert spec.description == ""
        assert spec.runtime == "Node.js 20"  # Default
        assert len(spec.endpoints) == 0
        assert len(spec.models) == 0
    
    def test_parse_defaults(self):
        """Test that default values are set correctly"""
        spec_content = """
# Service Name: Test API
Description: A test service

## Endpoints

### GET /health
- Description: Health check
"""
        
        spec = self.parser.parse(spec_content)
        
        assert spec.runtime == "Node.js 20"  # Default runtime
        assert spec.business_logic is None
        assert spec.database is None
        assert spec.deployment is None
        
        # Check endpoint defaults
        endpoint = spec.endpoints[0]
        assert endpoint['auth'] == 'None'
        assert endpoint['input'] is None
        assert endpoint['output'] is None


@pytest.fixture
def sample_spec_file(tmp_path):
    """Create a temporary specification file for testing"""
    content = """
# Service Name: Sample API
Description: A sample API for testing
Runtime: Node.js 20

## Endpoints

### GET /test
- Description: Test endpoint
- Output: Test response

## Models

### TestModel
- id: string
- value: string
"""
    
    spec_file = tmp_path / "test-spec.md"
    spec_file.write_text(content)
    return str(spec_file)


def test_parse_from_file(sample_spec_file):
    """Test parsing a specification from a file"""
    parser = SpecParser()
    
    with open(sample_spec_file, 'r') as f:
        content = f.read()
    
    spec = parser.parse(content)
    
    assert spec.name == "Sample API"
    assert spec.description == "A sample API for testing"
    assert len(spec.endpoints) == 1
    assert len(spec.models) == 1