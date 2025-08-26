"""
Google Cloud Platform provider for Cloud Run deployments.
"""
import subprocess
import os
from typing import Dict, List, Optional
import logging

from .base import CloudProvider, DeploymentError, ProviderFactory
from ..utils.security import sanitize_secrets


class GCPCloudRunProvider(CloudProvider):
    """Google Cloud Run deployment provider"""
    
    def __init__(self, project_id: str, region: str = 'us-central1', logger: Optional[logging.Logger] = None):
        super().__init__(project_id, region, logger)
        
        # Validate region format
        if self.region.endswith(('-a', '-b', '-c', '-d', '-e', '-f')):
            self.logger.warning(f"Region '{self.region}' looks like a zone. Removing zone suffix.")
            self.region = self.region[:-2]
    
    def deploy(self, service_name: str, source_dir: str) -> bool:
        """Deploy service to Cloud Run"""
        self.logger.info(f"Deploying {service_name} to Cloud Run")
        
        try:
            # Set project
            self._set_project()
            
            # Deploy to Cloud Run
            cmd = [
                'gcloud', 'run', 'deploy', service_name,
                '--source', source_dir,
                '--platform', 'managed',
                '--region', self.region,
                '--allow-unauthenticated',
                '--project', self.project_id
            ]
            
            self.logger.debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            self.logger.info("Deployment successful")
            self.logger.debug(f"Output: {sanitize_secrets(result.stdout)}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Deployment failed: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"Error output: {sanitize_secrets(str(e.stderr))}")
            
            # Try to get build logs
            self._log_build_errors(service_name)
            
            raise DeploymentError(error_msg) from e
    
    def get_service_url(self, service_name: str) -> str:
        """Get the public URL of a deployed service"""
        try:
            cmd = [
                'gcloud', 'run', 'services', 'describe', service_name,
                '--region', self.region,
                '--project', self.project_id,
                '--format', 'value(status.url)'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            url = result.stdout.strip()
            
            if not url:
                raise DeploymentError(f"Service {service_name} not found or not deployed")
            
            return url
            
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to get service URL: {e}") from e
    
    def get_logs(self, service_name: str, limit: int = 100) -> List[str]:
        """Get recent logs for a service"""
        try:
            cmd = [
                'gcloud', 'logs', 'read',
                f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service_name}"',
                '--project', self.project_id,
                '--limit', str(limit),
                '--format', 'value(textPayload)'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logs = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Sanitize logs before returning
            return [sanitize_secrets(log) for log in logs]
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get logs: {e}")
            return []
    
    def delete_service(self, service_name: str) -> bool:
        """Delete a deployed service"""
        try:
            cmd = [
                'gcloud', 'run', 'services', 'delete', service_name,
                '--region', self.region,
                '--project', self.project_id,
                '--quiet'
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Service {service_name} deleted successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to delete service: {e}")
            return False
    
    def list_services(self) -> List[Dict[str, str]]:
        """List all deployed services"""
        try:
            cmd = [
                'gcloud', 'run', 'services', 'list',
                '--region', self.region,
                '--project', self.project_id,
                '--format', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            import json
            services_data = json.loads(result.stdout)
            
            services = []
            for service in services_data:
                services.append({
                    'name': service.get('metadata', {}).get('name', ''),
                    'url': service.get('status', {}).get('url', ''),
                    'region': self.region,
                    'status': service.get('status', {}).get('conditions', [{}])[0].get('status', 'Unknown')
                })
            
            return services
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to list services: {e}")
            return []
    
    def validate_config(self) -> List[str]:
        """Validate GCP configuration"""
        errors = []
        
        # Check if gcloud is installed
        try:
            subprocess.run(['gcloud', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append("gcloud CLI not found. Please install Google Cloud SDK.")
        
        # Check authentication
        try:
            result = subprocess.run(
                ['gcloud', 'auth', 'list', '--filter=status:ACTIVE'], 
                capture_output=True, text=True, check=True
            )
            if 'ACTIVE' not in result.stdout:
                errors.append("No active gcloud authentication. Run 'gcloud auth login'.")
        except subprocess.CalledProcessError:
            errors.append("Unable to check gcloud authentication status.")
        
        # Check project access
        if self.project_id:
            try:
                subprocess.run(
                    ['gcloud', 'projects', 'describe', self.project_id], 
                    capture_output=True, check=True
                )
            except subprocess.CalledProcessError:
                errors.append(f"Unable to access project '{self.project_id}'. Check project ID and permissions.")
        
        return errors
    
    def _set_project(self):
        """Set the active gcloud project"""
        cmd = ['gcloud', 'config', 'set', 'project', self.project_id]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.logger.debug(f"Project set: {result.stderr}")
    
    def _log_build_errors(self, service_name: str):
        """Try to get and log build errors for debugging"""
        try:
            self.logger.info("Fetching build logs for debugging...")
            
            cmd = [
                'gcloud', 'builds', 'list',
                '--limit', '3',
                '--format', 'value(id)',
                '--project', self.project_id,
                '--sort-by', '~createTime'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                build_ids = result.stdout.strip().split('\n')
                
                for build_id in build_ids:
                    if build_id.strip():
                        log_cmd = [
                            'gcloud', 'builds', 'log', build_id.strip(),
                            '--project', self.project_id
                        ]
                        
                        log_result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=60)
                        
                        if log_result.returncode == 0:
                            sanitized_log = sanitize_secrets(log_result.stdout)
                            self.logger.error(f"Build log for {build_id}:")
                            self.logger.error(sanitized_log)
                            break
            
            # Provide helpful debugging link
            console_url = f"https://console.cloud.google.com/cloud-build/builds?project={self.project_id}"
            self.logger.info(f"For detailed logs visit: {console_url}")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch build logs: {e}")


# Register the provider
ProviderFactory.register('gcp', GCPCloudRunProvider)