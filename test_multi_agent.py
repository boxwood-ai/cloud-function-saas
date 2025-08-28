#!/usr/bin/env python3
"""
Test script for the multi-agent code generation system
"""

import os
import asyncio
from multi_agent_generator import MultiAgentCodeGenerator, create_multi_agent_generator
from spec_parser import SpecParser

def test_multi_agent_sync():
    """Test synchronous multi-agent code generation"""
    print("🧪 Testing Multi-Agent Code Generation (Sync)")
    
    # Load test spec
    spec_content = """# Service Name: Test API
Description: Simple test API for multi-agent validation
Runtime: Node.js 20

## Endpoints
### GET /health
- Description: Health check endpoint
- Output: {"status": "healthy"}

### GET /test
- Description: Simple test endpoint
- Output: {"message": "Hello World"}

## Models
### TestModel
- id: string (UUID)
- message: string
- timestamp: timestamp
"""
    
    try:
        # Parse spec
        parser = SpecParser()
        spec = parser.parse(spec_content)
        print(f"✅ Parsed spec: {spec.name}")
        
        # Generate with multi-agent system
        generator = create_multi_agent_generator(debug=True)
        generated_files = generator.generate_cloud_function(spec)
        
        print(f"✅ Generated {len(generated_files)} files:")
        for filename in generated_files.keys():
            print(f"   • {filename}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

async def test_multi_agent_async():
    """Test asynchronous multi-agent code generation"""
    print("\n🧪 Testing Multi-Agent Code Generation (Async)")
    
    # Load test spec
    spec_content = """# Service Name: Async Test API  
Description: Test API for async multi-agent validation
Runtime: Node.js 20

## Endpoints
### POST /users
- Description: Create a user
- Input: {"name": "string", "email": "string"}
- Output: {"user": "User", "id": "string"}

### GET /users/:id
- Description: Get user by ID
- Output: User object

## Models
### User
- id: string (UUID)
- name: string (required)
- email: string (required)
- createdAt: timestamp
"""
    
    try:
        # Parse spec
        parser = SpecParser()
        spec = parser.parse(spec_content)
        print(f"✅ Parsed spec: {spec.name}")
        
        # Generate with multi-agent system (async)
        generator = create_multi_agent_generator(debug=True)
        generated_files, validation = await generator.generate_cloud_function_async(spec)
        
        print(f"✅ Generated {len(generated_files)} files:")
        for filename in generated_files.keys():
            print(f"   • {filename}")
            
        print(f"📊 Validation Results:")
        print(f"   Score: {validation.score:.2f}")
        print(f"   Spec Compliance: {validation.spec_compliance:.2f}")
        print(f"   Issues: {len(validation.issues)}")
        print(f"   Passed: {validation.passed}")
        
        if validation.issues:
            print(f"   Top issues:")
            for issue in validation.issues[:3]:
                print(f"     - {issue}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_agent_components():
    """Test individual agent components"""
    print("\n🧪 Testing Individual Agent Components")
    
    try:
        from multi_agent_generator import CodeGeneratorAgent, ValidatorAgent
        import anthropic
        
        # Test agent initialization
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        model = "claude-sonnet-4-20250514"
        
        code_agent = CodeGeneratorAgent(client, model, debug=True)
        validator_agent = ValidatorAgent(client, model, debug=True)
        
        print("✅ Agents initialized successfully")
        print(f"   Code Generator: {code_agent.role.value}")
        print(f"   Validator: {validator_agent.role.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Multi-Agent Code Generation Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set in environment")
        return False
    
    results = []
    
    # Test 1: Component initialization
    results.append(test_agent_components())
    
    # Test 2: Synchronous generation
    results.append(test_multi_agent_sync())
    
    # Test 3: Asynchronous generation
    results.append(asyncio.run(test_multi_agent_async()))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    passed = sum(results)
    total = len(results)
    
    print(f"   Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Multi-agent system is working.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)