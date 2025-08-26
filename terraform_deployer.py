"""
Terraform deployment orchestration for multi-cloud deployments
"""

import os
import subprocess
import json
import shutil
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from utils import sanitize_secrets


class TerraformDeployer:
    """Deploy generated functions using Terraform to multiple cloud providers"""
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger('terraform_deployer')
        self.terraform_binary = self._find_terraform_binary()
        
    def _find_terraform_binary(self) -> str:
        """Find terraform binary in PATH"""
        terraform_path = shutil.which('terraform')
        if not terraform_path:
            raise RuntimeError(
                "Terraform binary not found in PATH. "
                "Please install Terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli"
            )
        
        self.logger.info(f"Found Terraform binary at: {terraform_path}")
        return terraform_path
    
    def validate_terraform_files(self) -> Tuple[bool, List[str]]:
        """Validate that required Terraform files exist and are syntactically correct"""
        required_files = ['main.tf', 'variables.tf', 'outputs.tf']
        missing_files = []
        errors = []
        
        # Check required files exist
        for file in required_files:
            file_path = self.project_dir / file
            if not file_path.exists():
                missing_files.append(file)
                errors.append(f"Missing required file: {file}")
        
        if missing_files:
            return False, errors
        
        # Validate Terraform syntax
        try:
            result = self._run_terraform_command(['validate'], capture_output=True)
            if result.returncode != 0:
                errors.append(f"Terraform validation failed: {result.stderr}")
                return False, errors
        except Exception as e:
            errors.append(f"Failed to run terraform validate: {e}")
            return False, errors
        
        self.logger.info("✅ Terraform files validation passed")
        return True, []
    
    def init_terraform(self, backend_config: Optional[Dict[str, str]] = None) -> bool:
        """Initialize Terraform working directory"""
        try:
            self.logger.info("Initializing Terraform...")
            
            cmd = ['init']
            if backend_config:
                for key, value in backend_config.items():
                    cmd.extend(['-backend-config', f'{key}={value}'])
            
            result = self._run_terraform_command(cmd)
            if result.returncode != 0:
                self.logger.error(f"Terraform init failed: {result.stderr}")
                return False
            
            self.logger.info("✅ Terraform initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Terraform: {e}")
            return False
    
    def plan_deployment(self, var_file: Optional[str] = None, variables: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        """Create Terraform execution plan"""
        try:
            self.logger.info("Creating Terraform plan...")
            
            cmd = ['plan', '-detailed-exitcode']
            
            if var_file:
                cmd.extend(['-var-file', var_file])
            
            if variables:
                for key, value in variables.items():
                    cmd.extend(['-var', f'{key}={value}'])
            
            result = self._run_terraform_command(cmd, capture_output=True)
            
            # Terraform plan exit codes: 0 = no changes, 1 = error, 2 = changes present
            if result.returncode == 0:
                self.logger.info("✅ Terraform plan completed - no changes needed")
                return True, "No changes needed"
            elif result.returncode == 2:
                self.logger.info("✅ Terraform plan completed - changes detected")
                return True, result.stdout
            else:
                self.logger.error(f"Terraform plan failed: {result.stderr}")
                return False, result.stderr
                
        except Exception as e:
            error_msg = f"Failed to create Terraform plan: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def apply_deployment(self, var_file: Optional[str] = None, variables: Optional[Dict[str, str]] = None, 
                        auto_approve: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """Apply Terraform configuration"""
        try:
            self.logger.info("Applying Terraform configuration...")
            
            cmd = ['apply']
            
            if auto_approve:
                cmd.append('-auto-approve')
            
            if var_file:
                cmd.extend(['-var-file', var_file])
            
            if variables:
                for key, value in variables.items():
                    cmd.extend(['-var', f'{key}={value}'])
            
            result = self._run_terraform_command(cmd)
            
            if result.returncode != 0:
                self.logger.error(f"Terraform apply failed: {result.stderr}")
                return False, {}
            
            # Get outputs after successful apply
            outputs = self.get_terraform_outputs()
            self.logger.info("✅ Terraform apply completed successfully")
            
            return True, outputs
            
        except Exception as e:
            error_msg = f"Failed to apply Terraform configuration: {e}"
            self.logger.error(error_msg)
            return False, {}
    
    def destroy_deployment(self, var_file: Optional[str] = None, variables: Optional[Dict[str, str]] = None,
                          auto_approve: bool = False) -> bool:
        """Destroy Terraform-managed infrastructure"""
        try:
            self.logger.info("Destroying Terraform-managed infrastructure...")
            
            cmd = ['destroy']
            
            if auto_approve:
                cmd.append('-auto-approve')
            
            if var_file:
                cmd.extend(['-var-file', var_file])
            
            if variables:
                for key, value in variables.items():
                    cmd.extend(['-var', f'{key}={value}'])
            
            result = self._run_terraform_command(cmd)
            
            if result.returncode != 0:
                self.logger.error(f"Terraform destroy failed: {result.stderr}")
                return False
            
            self.logger.info("✅ Terraform destroy completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to destroy Terraform infrastructure: {e}")
            return False
    
    def get_terraform_outputs(self) -> Dict[str, Any]:
        """Get Terraform outputs as JSON"""
        try:
            result = self._run_terraform_command(['output', '-json'], capture_output=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Failed to get Terraform outputs: {result.stderr}")
                return {}
            
            if not result.stdout.strip():
                self.logger.info("No Terraform outputs found")
                return {}
            
            outputs_raw = json.loads(result.stdout)
            
            # Extract values from Terraform output format
            outputs = {}
            for key, value_obj in outputs_raw.items():
                if isinstance(value_obj, dict) and 'value' in value_obj:
                    outputs[key] = value_obj['value']
                else:
                    outputs[key] = value_obj
            
            return outputs
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Terraform outputs JSON: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get Terraform outputs: {e}")
            return {}
    
    def get_terraform_state(self) -> Optional[Dict[str, Any]]:
        """Get current Terraform state"""
        try:
            result = self._run_terraform_command(['show', '-json'], capture_output=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Failed to get Terraform state: {result.stderr}")
                return None
            
            return json.loads(result.stdout) if result.stdout.strip() else None
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Terraform state JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get Terraform state: {e}")
            return None
    
    def refresh_state(self, var_file: Optional[str] = None, variables: Optional[Dict[str, str]] = None) -> bool:
        """Refresh Terraform state"""
        try:
            self.logger.info("Refreshing Terraform state...")
            
            cmd = ['refresh']
            
            if var_file:
                cmd.extend(['-var-file', var_file])
            
            if variables:
                for key, value in variables.items():
                    cmd.extend(['-var', f'{key}={value}'])
            
            result = self._run_terraform_command(cmd)
            
            if result.returncode != 0:
                self.logger.error(f"Terraform refresh failed: {result.stderr}")
                return False
            
            self.logger.info("✅ Terraform state refreshed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to refresh Terraform state: {e}")
            return False
    
    def workspace_list(self) -> List[str]:
        """List available Terraform workspaces"""
        try:
            result = self._run_terraform_command(['workspace', 'list'], capture_output=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Failed to list workspaces: {result.stderr}")
                return []
            
            # Parse workspace list output
            workspaces = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    workspaces.append(line)
                elif line.startswith('*'):
                    # Current workspace (remove * and whitespace)
                    workspaces.append(line[1:].strip())
            
            return workspaces
            
        except Exception as e:
            self.logger.error(f"Failed to list workspaces: {e}")
            return []
    
    def workspace_select(self, workspace: str) -> bool:
        """Select or create Terraform workspace"""
        try:
            # Try to select existing workspace
            result = self._run_terraform_command(['workspace', 'select', workspace], capture_output=True)
            
            if result.returncode == 0:
                self.logger.info(f"✅ Selected workspace: {workspace}")
                return True
            
            # If workspace doesn't exist, create it
            result = self._run_terraform_command(['workspace', 'new', workspace], capture_output=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to create workspace {workspace}: {result.stderr}")
                return False
            
            self.logger.info(f"✅ Created and selected workspace: {workspace}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to select/create workspace {workspace}: {e}")
            return False
    
    def check_terraform_version(self) -> Optional[str]:
        """Check Terraform version"""
        try:
            result = self._run_terraform_command(['version', '-json'], capture_output=True)
            
            if result.returncode != 0:
                # Fallback to plain version command
                result = self._run_terraform_command(['version'], capture_output=True)
                if result.returncode == 0:
                    # Parse version from plain output
                    for line in result.stdout.split('\n'):
                        if 'Terraform v' in line:
                            return line.strip()
                return None
            
            version_info = json.loads(result.stdout)
            return version_info.get('terraform_version', 'Unknown')
            
        except Exception as e:
            self.logger.error(f"Failed to check Terraform version: {e}")
            return None
    
    def _run_terraform_command(self, args: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run terraform command with proper environment and error handling"""
        
        cmd = [self.terraform_binary] + args
        
        # Set environment variables for cloud authentication
        env = os.environ.copy()
        
        # Ensure TF_IN_AUTOMATION for CI/CD environments
        env['TF_IN_AUTOMATION'] = 'true'
        
        # Set working directory
        cwd = str(self.project_dir)
        
        if self.logger and not capture_output:
            self.logger.debug(f"Running command in {cwd}: {' '.join(cmd)}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,  # Prevent hanging on interactive input
                    timeout=1800  # 30 minutes timeout
                )
            else:
                # For interactive commands, don't capture output
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    env=env,
                    stdin=subprocess.DEVNULL,  # Prevent hanging on interactive input
                    timeout=1800  # 30 minutes timeout
                )
                # Create a mock result for consistency
                result.stdout = ""
                result.stderr = ""
            
            return result
            
        except subprocess.TimeoutExpired:
            error_msg = f"Terraform command timed out after 30 minutes: {' '.join(cmd)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Failed to run terraform command {' '.join(cmd)}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def deploy(self, service_name: str, providers: List[str], var_file: Optional[str] = None, 
               variables: Optional[Dict[str, str]] = None, auto_approve: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """Complete deployment workflow: init -> plan -> apply"""
        
        self.logger.info(f"🚀 Starting Terraform deployment for {service_name}")
        self.logger.info(f"Target providers: {', '.join(providers)}")
        
        # Step 1: Validate Terraform files
        valid, errors = self.validate_terraform_files()
        if not valid:
            self.logger.error("Terraform validation failed:")
            for error in errors:
                self.logger.error(f"  • {error}")
            return False, {}
        
        # Step 2: Initialize Terraform
        if not self.init_terraform():
            return False, {}
        
        # Step 3: Create execution plan
        plan_success, plan_output = self.plan_deployment(var_file, variables)
        if not plan_success:
            self.logger.error("Terraform planning failed")
            return False, {}
        
        # Step 4: Apply configuration
        apply_success, outputs = self.apply_deployment(var_file, variables, auto_approve)
        if not apply_success:
            return False, {}
        
        # Log deployment summary
        self.logger.info("🎉 Terraform deployment completed successfully!")
        
        if outputs:
            self.logger.info("📊 Deployment outputs:")
            for key, value in outputs.items():
                if isinstance(value, str) and ('http' in value or 'https' in value):
                    self.logger.info(f"  🌐 {key}: {value}")
                else:
                    # Sanitize sensitive information
                    safe_value = sanitize_secrets(str(value))
                    self.logger.info(f"  • {key}: {safe_value}")
        
        return True, outputs