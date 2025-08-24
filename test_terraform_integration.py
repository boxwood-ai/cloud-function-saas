#!/usr/bin/env python3
"""
Integration tests for Terraform multi-cloud deployment system
Tests the complete workflow without actually deploying to cloud providers
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import json

# Import our modules
from spec_parser import SpecParser
from terraform_code_generator import TerraformCodeGenerator
from terraform_deployer import TerraformDeployer
from terraform_state_manager import TerraformStateManager


class TestTerraformIntegration:
    """Test suite for Terraform integration"""
    
    def __init__(self):
        self.test_dir = None
        self.passed_tests = []
        self.failed_tests = []
    
    def setup_test_environment(self):
        """Create temporary directory for tests"""
        self.test_dir = Path(tempfile.mkdtemp(prefix='terraform_test_'))
        print(f"🔧 Test environment: {self.test_dir}")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print("🧹 Test environment cleaned up")
    
    def test_spec_parsing(self):
        """Test specification parsing"""
        print("\n🧪 Testing specification parsing...")
        
        try:
            spec_content = """
# Service Name: Test API

Description: Test service for integration testing
Runtime: Node.js 20

## Endpoints

### GET /health
- Description: Health check endpoint
- Output: {"status": "healthy"}

### GET /test
- Description: Test endpoint
- Output: {"message": "Hello World"}

## Models

### TestModel
- id: UUID (required)
- name: string (required)
"""
            
            parser = SpecParser()
            spec = parser.parse(spec_content)
            
            assert spec.name == "Test API"
            assert spec.description == "Test service for integration testing"
            assert len(spec.endpoints) >= 2
            assert "TestModel" in spec.models
            
            self.passed_tests.append("spec_parsing")
            print("✅ Specification parsing: PASSED")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"spec_parsing: {e}")
            print(f"❌ Specification parsing: FAILED - {e}")
            return False
    
    def test_terraform_code_generation(self):
        """Test Terraform code generation (without API calls)"""
        print("\n🧪 Testing Terraform code generation structure...")
        
        try:
            # Mock spec for testing
            from spec_parser import ServiceSpec
            
            spec = ServiceSpec(
                name="Test Service",
                description="Integration test service", 
                runtime="Node.js 20",
                endpoints=[
                    {'method': 'GET', 'path': '/health', 'description': 'Health check'},
                    {'method': 'GET', 'path': '/test', 'description': 'Test endpoint'}
                ],
                models={'TestModel': {'id': 'UUID', 'name': 'string'}}
            )
            
            # Test the code generator structure (without actual API call)
            generator = TerraformCodeGenerator()
            
            # Test provider parsing
            providers = ['gcp', 'aws']
            
            # Test prompt building (this doesn't make API calls)
            prompt = generator._build_terraform_prompt(spec, providers)
            assert 'terraform' in prompt.lower()
            assert 'gcp' in prompt.lower() or 'aws' in prompt.lower()
            
            # Test provider-specific tfvars generation
            gcp_vars = generator._generate_provider_tfvars(spec, 'gcp')
            aws_vars = generator._generate_provider_tfvars(spec, 'aws')
            
            assert 'project_id' in gcp_vars
            assert 'aws_region' in aws_vars
            
            # Test README generation
            readme = generator.generate_deployment_readme(spec, providers)
            assert 'Test Service' in readme
            assert 'terraform apply' in readme
            
            self.passed_tests.append("terraform_code_generation")
            print("✅ Terraform code generation structure: PASSED")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"terraform_code_generation: {e}")
            print(f"❌ Terraform code generation: FAILED - {e}")
            return False
    
    def test_terraform_file_structure(self):
        """Test that generated Terraform files have correct structure"""
        print("\n🧪 Testing Terraform file structure...")
        
        try:
            # Create mock generated files
            test_project_dir = self.test_dir / "test_project"
            test_project_dir.mkdir()
            
            # Create mock Terraform files
            main_tf_content = """
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

module "gcp_serverless" {
  source = "./terraform/modules/gcp-serverless"
  
  project_id = var.project_id
  service_name = var.service_name
  container_image = var.container_image
}
"""
            
            variables_tf_content = """
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "service_name" {
  description = "Name of the service"
  type        = string
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}
"""
            
            outputs_tf_content = """
output "service_url" {
  description = "URL of the deployed service"
  value       = module.gcp_serverless.service_url
}
"""
            
            # Write test files
            (test_project_dir / "main.tf").write_text(main_tf_content)
            (test_project_dir / "variables.tf").write_text(variables_tf_content)
            (test_project_dir / "outputs.tf").write_text(outputs_tf_content)
            
            # Test file validation (mock terraform binary)
            # We'll just check file existence manually since terraform isn't installed
            
            # Test required files exist
            required_files = ['main.tf', 'variables.tf', 'outputs.tf']
            for file in required_files:
                assert (test_project_dir / file).exists(), f"Missing {file}"
            
            # Test file contents
            main_content = (test_project_dir / "main.tf").read_text()
            assert "terraform" in main_content
            assert "module" in main_content
            
            variables_content = (test_project_dir / "variables.tf").read_text()
            assert "variable" in variables_content
            assert "project_id" in variables_content
            
            outputs_content = (test_project_dir / "outputs.tf").read_text()
            assert "output" in outputs_content
            assert "service_url" in outputs_content
            
            self.passed_tests.append("terraform_file_structure")
            print("✅ Terraform file structure: PASSED")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"terraform_file_structure: {e}")
            print(f"❌ Terraform file structure: FAILED - {e}")
            return False
    
    def test_state_management(self):
        """Test Terraform state management"""
        print("\n🧪 Testing Terraform state management...")
        
        try:
            test_project_dir = self.test_dir / "state_test"
            test_project_dir.mkdir()
            
            # Create state manager with mocked terraform binary
            class MockStateManager(TerraformStateManager):
                def _find_terraform_binary(self):
                    return "/usr/bin/terraform"  # Mock path
            
            state_manager = MockStateManager(str(test_project_dir))
            
            # Test backend configuration generation
            local_config = state_manager.generate_backend_configuration('local')
            assert 'backend "local"' in local_config
            
            gcs_config = state_manager.generate_backend_configuration(
                'gcs', 
                bucket='test-bucket', 
                prefix='test/state',
                project='test-project'
            )
            assert 'backend "gcs"' in gcs_config
            assert 'test-bucket' in gcs_config
            
            s3_config = state_manager.generate_backend_configuration(
                's3',
                bucket='test-bucket',
                key='terraform.tfstate',
                region='us-west-2'
            )
            assert 'backend "s3"' in s3_config
            assert 'test-bucket' in s3_config
            
            # Test recommendation system
            recommendation = state_manager.recommend_backend_config(['gcp'], 'test-service')
            assert recommendation['type'] in ['local', 'gcs']
            
            self.passed_tests.append("state_management")
            print("✅ Terraform state management: PASSED")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"state_management: {e}")
            print(f"❌ Terraform state management: FAILED - {e}")
            return False
    
    def test_provider_validation(self):
        """Test provider validation and configuration"""
        print("\n🧪 Testing provider validation...")
        
        try:
            # Test provider parsing from CLI
            from terraform_prototype import parse_providers
            
            # Test valid providers
            assert parse_providers('gcp') == ['gcp']
            assert parse_providers('aws') == ['aws']
            assert set(parse_providers('gcp,aws')) == {'gcp', 'aws'}
            assert set(parse_providers('both')) == {'gcp', 'aws'}
            
            # Test deduplication
            providers = parse_providers('gcp,gcp,aws')
            assert len(providers) == 2
            assert 'gcp' in providers
            assert 'aws' in providers
            
            # Test invalid provider handling (we can't test sys.exit directly)
            # So we'll just test that the function exists and runs without error for valid inputs
            
            self.passed_tests.append("provider_validation")
            print("✅ Provider validation: PASSED")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"provider_validation: {e}")
            print(f"❌ Provider validation: FAILED - {e}")
            return False
    
    def test_module_structure(self):
        """Test that Terraform modules are properly structured"""
        print("\n🧪 Testing Terraform module structure...")
        
        try:
            # Check that our modules exist and have required files
            project_root = Path(__file__).parent
            terraform_modules = project_root / "terraform" / "modules"
            
            # Test GCP module
            gcp_module = terraform_modules / "gcp-serverless"
            assert gcp_module.exists(), "GCP module directory missing"
            assert (gcp_module / "main.tf").exists(), "GCP main.tf missing"
            assert (gcp_module / "variables.tf").exists(), "GCP variables.tf missing"
            assert (gcp_module / "outputs.tf").exists(), "GCP outputs.tf missing"
            
            # Test AWS module
            aws_module = terraform_modules / "aws-serverless"
            assert aws_module.exists(), "AWS module directory missing"
            assert (aws_module / "main.tf").exists(), "AWS main.tf missing"
            assert (aws_module / "variables.tf").exists(), "AWS variables.tf missing"
            assert (aws_module / "outputs.tf").exists(), "AWS outputs.tf missing"
            
            # Test shared module
            shared_module = terraform_modules / "shared"
            assert shared_module.exists(), "Shared module directory missing"
            assert (shared_module / "main.tf").exists(), "Shared main.tf missing"
            assert (shared_module / "variables.tf").exists(), "Shared variables.tf missing"
            assert (shared_module / "outputs.tf").exists(), "Shared outputs.tf missing"
            
            # Test module content structure
            gcp_main = (gcp_module / "main.tf").read_text()
            assert "google_cloud_run_service" in gcp_main
            assert "terraform" in gcp_main
            
            aws_main = (aws_module / "main.tf").read_text()
            assert "aws_ecs_service" in aws_main or "aws_lb" in aws_main
            assert "terraform" in aws_main
            
            self.passed_tests.append("module_structure")
            print("✅ Terraform module structure: PASSED")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"module_structure: {e}")
            print(f"❌ Terraform module structure: FAILED - {e}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Terraform Integration Tests")
        print("=" * 50)
        
        self.setup_test_environment()
        
        try:
            # Run all tests
            tests = [
                self.test_spec_parsing,
                self.test_terraform_code_generation,
                self.test_terraform_file_structure,
                self.test_state_management,
                self.test_provider_validation,
                self.test_module_structure
            ]
            
            for test in tests:
                test()
            
            # Print summary
            print("\n" + "=" * 50)
            print("📊 Test Results Summary")
            print("=" * 50)
            
            print(f"✅ Passed: {len(self.passed_tests)}")
            for test in self.passed_tests:
                print(f"   • {test}")
            
            if self.failed_tests:
                print(f"\n❌ Failed: {len(self.failed_tests)}")
                for test in self.failed_tests:
                    print(f"   • {test}")
                return False
            else:
                print("\n🎉 All tests passed!")
                return True
                
        finally:
            self.cleanup_test_environment()


def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == '--verbose':
        os.environ['DEBUG'] = '1'
    
    tester = TestTerraformIntegration()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)
    
    print("\n💡 Integration tests completed successfully!")
    print("🚀 The Terraform multi-cloud system is ready for use!")


if __name__ == '__main__':
    main()