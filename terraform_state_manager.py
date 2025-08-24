"""
Terraform State Management for Cloud Function SaaS
Handles local and remote state configuration, backend setup, and state operations
"""

import os
import json
import subprocess
from typing import Dict, Optional, List, Tuple, Any
from pathlib import Path
import tempfile
import shutil

from utils import sanitize_secrets


class TerraformStateManager:
    """Manages Terraform state configuration and operations"""
    
    def __init__(self, project_dir: str, logger=None):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self.terraform_binary = self._find_terraform_binary()
    
    def _find_terraform_binary(self) -> str:
        """Find terraform binary in PATH"""
        terraform_path = shutil.which('terraform')
        if not terraform_path:
            raise RuntimeError("Terraform binary not found in PATH")
        return terraform_path
    
    def setup_local_state(self) -> Dict[str, str]:
        """Configure local state backend"""
        backend_config = {
            'path': str(self.project_dir / 'terraform.tfstate')
        }
        
        if self.logger:
            self.logger.info("Configured local state backend")
        
        return backend_config
    
    def setup_gcs_state(self, bucket: str, prefix: str = "", project: str = "") -> Dict[str, str]:
        """Configure Google Cloud Storage remote state backend"""
        backend_config = {
            'bucket': bucket,
            'prefix': prefix or 'terraform/state'
        }
        
        if project:
            backend_config['project'] = project
        
        # Verify bucket exists and is accessible
        try:
            result = subprocess.run(
                ['gsutil', 'ls', f'gs://{bucket}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                if self.logger:
                    self.logger.warning(f"Cannot access GCS bucket {bucket}: {result.stderr}")
                return {}
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            if self.logger:
                self.logger.warning("gsutil not found or timed out, skipping bucket verification")
        
        if self.logger:
            self.logger.info(f"Configured GCS remote state backend: gs://{bucket}/{prefix}")
        
        return backend_config
    
    def setup_s3_state(self, bucket: str, key: str, region: str = "us-west-2", 
                      dynamodb_table: str = "") -> Dict[str, str]:
        """Configure AWS S3 remote state backend"""
        backend_config = {
            'bucket': bucket,
            'key': key,
            'region': region
        }
        
        if dynamodb_table:
            backend_config['dynamodb_table'] = dynamodb_table
        
        # Verify bucket exists and is accessible
        try:
            result = subprocess.run(
                ['aws', 's3api', 'head-bucket', '--bucket', bucket],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                if self.logger:
                    self.logger.warning(f"Cannot access S3 bucket {bucket}: {result.stderr}")
                return {}
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            if self.logger:
                self.logger.warning("AWS CLI not found or timed out, skipping bucket verification")
        
        if self.logger:
            self.logger.info(f"Configured S3 remote state backend: s3://{bucket}/{key}")
        
        return backend_config
    
    def setup_azurerm_state(self, resource_group_name: str, storage_account_name: str, 
                           container_name: str, key: str) -> Dict[str, str]:
        """Configure Azure Storage remote state backend"""
        backend_config = {
            'resource_group_name': resource_group_name,
            'storage_account_name': storage_account_name,
            'container_name': container_name,
            'key': key
        }
        
        if self.logger:
            self.logger.info(f"Configured Azure Storage remote state backend: {storage_account_name}/{container_name}")
        
        return backend_config
    
    def generate_backend_configuration(self, backend_type: str, **kwargs) -> str:
        """Generate Terraform backend configuration block"""
        
        if backend_type == 'local':
            return '''
terraform {
  backend "local" {}
}
'''
        
        elif backend_type == 'gcs':
            bucket = kwargs.get('bucket', '')
            prefix = kwargs.get('prefix', 'terraform/state')
            project = kwargs.get('project', '')
            
            config = f'''
terraform {{
  backend "gcs" {{
    bucket = "{bucket}"
    prefix = "{prefix}"'''
            
            if project:
                config += f'\n    project = "{project}"'
            
            config += '''
  }
}
'''
            return config
        
        elif backend_type == 's3':
            bucket = kwargs.get('bucket', '')
            key = kwargs.get('key', 'terraform.tfstate')
            region = kwargs.get('region', 'us-west-2')
            dynamodb_table = kwargs.get('dynamodb_table', '')
            
            config = f'''
terraform {{
  backend "s3" {{
    bucket = "{bucket}"
    key    = "{key}"
    region = "{region}"'''
            
            if dynamodb_table:
                config += f'\n    dynamodb_table = "{dynamodb_table}"'
            
            config += '''
  }
}
'''
            return config
        
        elif backend_type == 'azurerm':
            resource_group_name = kwargs.get('resource_group_name', '')
            storage_account_name = kwargs.get('storage_account_name', '')
            container_name = kwargs.get('container_name', '')
            key = kwargs.get('key', 'terraform.tfstate')
            
            return f'''
terraform {{
  backend "azurerm" {{
    resource_group_name  = "{resource_group_name}"
    storage_account_name = "{storage_account_name}"
    container_name       = "{container_name}"
    key                  = "{key}"
  }}
}}
'''
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
    
    def create_state_bucket_gcs(self, bucket_name: str, project_id: str, location: str = "US") -> bool:
        """Create GCS bucket for Terraform state storage"""
        try:
            # Check if bucket exists
            result = subprocess.run(
                ['gsutil', 'ls', f'gs://{bucket_name}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if self.logger:
                    self.logger.info(f"GCS bucket {bucket_name} already exists")
                return True
            
            # Create bucket
            result = subprocess.run(
                ['gsutil', 'mb', '-p', project_id, '-c', 'STANDARD', '-l', location, f'gs://{bucket_name}'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                if self.logger:
                    self.logger.error(f"Failed to create GCS bucket: {result.stderr}")
                return False
            
            # Enable versioning
            subprocess.run(
                ['gsutil', 'versioning', 'set', 'on', f'gs://{bucket_name}'],
                capture_output=True,
                timeout=30
            )
            
            if self.logger:
                self.logger.info(f"Created GCS bucket {bucket_name} with versioning enabled")
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            if self.logger:
                self.logger.error(f"Failed to create GCS bucket: {e}")
            return False
    
    def create_state_bucket_s3(self, bucket_name: str, region: str = "us-west-2") -> bool:
        """Create S3 bucket for Terraform state storage"""
        try:
            # Check if bucket exists
            result = subprocess.run(
                ['aws', 's3api', 'head-bucket', '--bucket', bucket_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if self.logger:
                    self.logger.info(f"S3 bucket {bucket_name} already exists")
                return True
            
            # Create bucket
            if region == 'us-east-1':
                # us-east-1 doesn't need location constraint
                result = subprocess.run(
                    ['aws', 's3api', 'create-bucket', '--bucket', bucket_name],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            else:
                result = subprocess.run(
                    ['aws', 's3api', 'create-bucket', '--bucket', bucket_name, 
                     '--create-bucket-configuration', f'LocationConstraint={region}'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            
            if result.returncode != 0:
                if self.logger:
                    self.logger.error(f"Failed to create S3 bucket: {result.stderr}")
                return False
            
            # Enable versioning
            subprocess.run(
                ['aws', 's3api', 'put-bucket-versioning', '--bucket', bucket_name,
                 '--versioning-configuration', 'Status=Enabled'],
                capture_output=True,
                timeout=30
            )
            
            # Enable encryption
            subprocess.run(
                ['aws', 's3api', 'put-bucket-encryption', '--bucket', bucket_name,
                 '--server-side-encryption-configuration', 
                 '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'],
                capture_output=True,
                timeout=30
            )
            
            if self.logger:
                self.logger.info(f"Created S3 bucket {bucket_name} with versioning and encryption")
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            if self.logger:
                self.logger.error(f"Failed to create S3 bucket: {e}")
            return False
    
    def create_dynamodb_lock_table(self, table_name: str, region: str = "us-west-2") -> bool:
        """Create DynamoDB table for Terraform state locking"""
        try:
            # Check if table exists
            result = subprocess.run(
                ['aws', 'dynamodb', 'describe-table', '--table-name', table_name, '--region', region],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if self.logger:
                    self.logger.info(f"DynamoDB table {table_name} already exists")
                return True
            
            # Create table
            result = subprocess.run([
                'aws', 'dynamodb', 'create-table',
                '--table-name', table_name,
                '--attribute-definitions', 'AttributeName=LockID,AttributeType=S',
                '--key-schema', 'AttributeName=LockID,KeyType=HASH',
                '--provisioned-throughput', 'ReadCapacityUnits=1,WriteCapacityUnits=1',
                '--region', region
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                if self.logger:
                    self.logger.error(f"Failed to create DynamoDB table: {result.stderr}")
                return False
            
            if self.logger:
                self.logger.info(f"Created DynamoDB table {table_name} for state locking")
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            if self.logger:
                self.logger.error(f"Failed to create DynamoDB table: {e}")
            return False
    
    def migrate_state_to_remote(self, backend_type: str, backend_config: Dict[str, str]) -> bool:
        """Migrate local state to remote backend"""
        try:
            if self.logger:
                self.logger.info(f"Migrating state to {backend_type} backend...")
            
            # Create a backup of current state
            local_state_path = self.project_dir / 'terraform.tfstate'
            if local_state_path.exists():
                backup_path = self.project_dir / f'terraform.tfstate.backup.{int(os.time.time())}'
                shutil.copy2(local_state_path, backup_path)
                if self.logger:
                    self.logger.info(f"Created state backup: {backup_path}")
            
            # Update backend configuration
            backend_tf_path = self.project_dir / 'backend.tf'
            backend_config_str = self.generate_backend_configuration(backend_type, **backend_config)
            
            with open(backend_tf_path, 'w') as f:
                f.write(backend_config_str)
            
            # Reinitialize with new backend
            result = subprocess.run(
                [self.terraform_binary, 'init', '-migrate-state', '-force-copy'],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                if self.logger:
                    self.logger.error(f"State migration failed: {result.stderr}")
                return False
            
            if self.logger:
                self.logger.info("State migration completed successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to migrate state: {e}")
            return False
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get information about current Terraform state"""
        try:
            # Get state list
            result = subprocess.run(
                [self.terraform_binary, 'state', 'list'],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return {'error': 'Could not list state resources'}
            
            resources = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Get backend configuration
            try:
                with open(self.project_dir / '.terraform' / 'terraform.tfstate', 'r') as f:
                    terraform_state = json.load(f)
                    backend_config = terraform_state.get('backend', {})
            except (FileNotFoundError, json.JSONDecodeError):
                backend_config = {'type': 'local'}
            
            return {
                'resource_count': len(resources),
                'resources': resources,
                'backend': backend_config
            }
            
        except Exception as e:
            return {'error': f'Failed to get state info: {e}'}
    
    def lock_state(self) -> bool:
        """Manually lock Terraform state (for debugging)"""
        try:
            result = subprocess.run(
                [self.terraform_binary, 'force-unlock', '-force', 'manual-lock'],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def unlock_state(self, lock_id: str = "") -> bool:
        """Unlock Terraform state"""
        try:
            if lock_id:
                cmd = [self.terraform_binary, 'force-unlock', '-force', lock_id]
            else:
                cmd = [self.terraform_binary, 'force-unlock', '-force', 'auto']
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def recommend_backend_config(self, providers: List[str], service_name: str) -> Dict[str, Any]:
        """Recommend backend configuration based on providers and service name"""
        
        # Default to local for development
        recommendation = {
            'type': 'local',
            'reason': 'Default local backend for development',
            'config': {}
        }
        
        # If deploying to GCP, recommend GCS backend
        if 'gcp' in providers:
            try:
                # Try to get current project
                result = subprocess.run(
                    ['gcloud', 'config', 'get-value', 'project'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    project_id = result.stdout.strip()
                    bucket_name = f"{project_id}-terraform-state"
                    
                    recommendation = {
                        'type': 'gcs',
                        'reason': 'GCS backend recommended for GCP deployment',
                        'config': {
                            'bucket': bucket_name,
                            'prefix': f'cloud-function-saas/{service_name}',
                            'project': project_id
                        }
                    }
            except Exception:
                pass
        
        # If deploying to AWS (and not GCP), recommend S3 backend
        elif 'aws' in providers:
            try:
                # Try to get current AWS account
                result = subprocess.run(
                    ['aws', 'sts', 'get-caller-identity', '--output', 'json'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    account_info = json.loads(result.stdout)
                    account_id = account_info.get('Account', '')
                    
                    if account_id:
                        bucket_name = f"terraform-state-{account_id}"
                        
                        recommendation = {
                            'type': 's3',
                            'reason': 'S3 backend recommended for AWS deployment',
                            'config': {
                                'bucket': bucket_name,
                                'key': f'cloud-function-saas/{service_name}/terraform.tfstate',
                                'region': 'us-west-2',
                                'dynamodb_table': 'terraform-state-lock'
                            }
                        }
            except Exception:
                pass
        
        return recommendation