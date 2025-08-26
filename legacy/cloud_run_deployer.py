"""
Cloud Run deployment components for the Cloud Function Generator
"""

import os
import subprocess
import traceback
import logging
from typing import Optional, Dict, Any

from google.cloud import run_v2
from google.cloud.devtools import cloudbuild_v1
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from utils import sanitize_secrets


class CloudRunDeployer:
    """Deploy generated functions to Google Cloud Run"""
    
    def __init__(self, project_id: Optional[str] = None, region: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = region or os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        self.logger = logger or logging.getLogger('cloud_function_generator')
        
        # Initialize Google Cloud clients with ADC
        self.credentials = None
        self.run_client = None
        self.build_client = None
        
        try:
            self.credentials, detected_project = default()
            if not self.project_id and detected_project:
                self.project_id = detected_project
                self.logger.info(f"Using project from ADC: {self.project_id}")
            
            self.run_client = run_v2.ServicesClient(credentials=self.credentials)
            self.build_client = cloudbuild_v1.CloudBuildClient(credentials=self.credentials)
            self.logger.info("Successfully initialized Google Cloud clients with ADC")
        except DefaultCredentialsError:
            self.logger.warning("ADC not available, falling back to gcloud CLI")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Google Cloud clients: {e}")
        
        self.logger.info(f"CloudRunDeployer initialized with project_id='{self.project_id}', region='{self.region}'")
        
        # Validate region format (should not include zone suffix like -a, -b, -c)
        if self.region and self.region.endswith(('-a', '-b', '-c', '-d', '-e', '-f')):
            warning_msg = f"Region '{self.region}' looks like a zone. Removing zone suffix for Cloud Run."
            print(f"⚠️  Warning: {warning_msg}")
            self.logger.warning(warning_msg)
            self.region = self.region[:-2]  # Remove zone suffix
            self.logger.info(f"Region corrected to: {self.region}")
    
    def deploy(self, service_name: str, source_dir: str) -> bool:
        """Deploy to Cloud Run using client libraries or fallback to gcloud CLI"""
        self.logger.info("=" * 40)
        self.logger.info("STARTING CLOUD RUN DEPLOYMENT")
        self.logger.info("=" * 40)
        self.logger.info(f"Service name: {service_name}")
        self.logger.info(f"Project: {self.project_id}")
        self.logger.info(f"Region: {self.region}")
        self.logger.info(f"Source directory: {source_dir}")
        
        # Try using client libraries first, fallback to gcloud CLI
        if self.run_client and self.build_client:
            try:
                return self._deploy_with_client_libraries(service_name, source_dir)
            except Exception as e:
                self.logger.warning(f"Client library deployment failed: {e}")
                self.logger.info("Falling back to gcloud CLI deployment")
        
        return self._deploy_with_gcloud_cli(service_name, source_dir)
    
    def _deploy_with_client_libraries(self, service_name: str, source_dir: str) -> bool:
        """Deploy using Google Cloud client libraries"""
        self.logger.info("Using Google Cloud client libraries for deployment")
        
        # For now, we'll use a hybrid approach - use client libraries for monitoring
        # but still use gcloud for the actual deployment since it's more robust
        # This gives us the benefits of ADC while maintaining reliability
        
        try:
            # Check if service already exists
            service_path = f"projects/{self.project_id}/locations/{self.region}/services/{service_name}"
            try:
                existing_service = self.run_client.get_service(name=service_path)
                self.logger.info(f"Service {service_name} already exists, will update")
            except Exception:
                self.logger.info(f"Service {service_name} does not exist, will create new")
            
            # Use gcloud for actual deployment (more reliable for source-based deployments)
            return self._deploy_with_gcloud_cli(service_name, source_dir)
            
        except Exception as e:
            self.logger.error(f"Client library deployment error: {e}")
            raise
    
    def _deploy_with_gcloud_cli(self, service_name: str, source_dir: str) -> bool:
        """Deploy using gcloud CLI (fallback method)"""
        self.logger.info("Using gcloud CLI for deployment")
        
        try:
            # Set project (done silently within the spinner)
            self.logger.info("Setting gcloud project...")
            set_project_cmd = ['gcloud', 'config', 'set', 'project', self.project_id]
            self.logger.debug(f"Running command: {' '.join(set_project_cmd)}")
            
            result = subprocess.run(set_project_cmd, check=True, capture_output=True, text=True)
            self.logger.debug(f"Set project result - stdout: {result.stdout}, stderr: {result.stderr}, returncode: {result.returncode}")
            
            if result.stdout.strip():
                success_msg = f"Project set: {result.stdout.strip()}"
                self.logger.info(success_msg)
            
            # Deploy to Cloud Run (done within the spinner)
            self.logger.info("Starting Cloud Run deployment...")
            cmd = [
                'gcloud', 'run', 'deploy', service_name,
                '--source', source_dir,
                '--platform', 'managed',
                '--region', self.region,
                '--allow-unauthenticated'
            ]
            self.logger.info(f"Running deployment command: {' '.join(cmd)}")
            
            # Run deployment with timeout
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
                return_code = result.returncode
                full_output = result.stdout + result.stderr
                
                # Log all output for debugging
                if full_output:
                    for line in full_output.split('\n'):
                        if line.strip():
                            self.logger.debug(f"Deploy output: {line.strip()}")
                
            except subprocess.TimeoutExpired:
                self.logger.error("Deployment timed out after 10 minutes")
                raise
            
            self.logger.debug(f"Process completed with return code: {return_code}")
            
            if return_code == 0:
                self.logger.info("Deployment completed successfully")
                self.logger.debug(f"Full deployment output:\n{full_output}")
                return True
            else:
                raise subprocess.CalledProcessError(return_code, cmd, full_output)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Deployment failed with exit code {e.returncode}"
            print(f"\n❌ {error_msg}")
            print(f"Command that failed: {' '.join(e.cmd)}")
            self.logger.error(error_msg)
            self.logger.error(f"Failed command: {' '.join(e.cmd)}")
            
            if e.output:
                sanitized_output = sanitize_secrets(str(e.output))
                print(f"Command output: {sanitized_output}")
                self.logger.error(f"Command output:\n{sanitized_output}")
            if hasattr(e, 'stdout') and e.stdout:
                sanitized_stdout = sanitize_secrets(str(e.stdout))
                print(f"Standard output: {sanitized_stdout}")
                self.logger.error(f"Standard output:\n{sanitized_stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                sanitized_stderr = sanitize_secrets(str(e.stderr))
                print(f"Error output: {sanitized_stderr}")
                self.logger.error(f"Error output:\n{sanitized_stderr}")
            
            self.logger.error(f"Full exception details: {traceback.format_exc()}")
            
            # Show debugging help
            print(f"\n🔍 For detailed build logs and debugging:")
            print(f"   • Visit: https://console.cloud.google.com/cloud-build/builds?project={self.project_id}")
            print(f"   • Look for the most recent failed build")
            print(f"   • Check build steps for specific error details")
            
            # Try to fetch build logs for more details
            self._fetch_build_logs(service_name)
            return False
        except subprocess.TimeoutExpired:
            error_msg = "Deployment timed out after 10 minutes"
            print(f"\n❌ {error_msg}")
            print("💡 The deployment is taking longer than expected. This might be due to:")
            print("   • Large Docker image build times")
            print("   • Network connectivity issues")
            print("   • Google Cloud Build queue delays")
            print(f"💡 You can check the status manually with: gcloud run services list --project={self.project_id}")
            self.logger.error(error_msg)
            return False
        except FileNotFoundError:
            error_msg = "gcloud command not found!"
            print(f"\n❌ Error: {error_msg}")
            print("💡 Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
            self.logger.error(error_msg)
            self.logger.error("Google Cloud SDK not installed or not in PATH")
            return False
        except Exception as e:
            error_msg = f"Unexpected deployment error: {e}"
            print(f"\n❌ {error_msg}")
            self.logger.error(error_msg)
            self.logger.error(f"Full exception details: {traceback.format_exc()}")
            return False
    
    def _fetch_build_logs(self, service_name: str):
        """Fetch and display recent build logs to help debug deployment failures"""
        self.logger.info("Attempting to fetch build logs for debugging...")
        
        # Try using client libraries first, fallback to gcloud CLI
        if self.build_client:
            try:
                self._fetch_build_logs_with_client(service_name)
                return
            except Exception as e:
                self.logger.warning(f"Failed to fetch build logs with client libraries: {e}")
                self.logger.info("Falling back to gcloud CLI for build logs")
        
        self._fetch_build_logs_with_gcloud(service_name)
    
    def _fetch_build_logs_with_client(self, service_name: str):
        """Fetch build logs using Cloud Build client library"""
        self.logger.info("Fetching build logs using client library")
        
        try:
            print("\n📜 Fetching recent build logs for debugging...")
            
            # List recent builds
            parent = f"projects/{self.project_id}"
            request = cloudbuild_v1.ListBuildsRequest(
                parent=parent,
                page_size=3,
                filter=f'status="FAILURE" OR status="SUCCESS"'
            )
            
            builds = self.build_client.list_builds(request=request)
            build_list = list(builds)
            
            if build_list:
                print(f"   Found recent builds: {len(build_list)}")
                self.logger.info(f"Found {len(build_list)} recent builds")
                
                # Get logs for the most recent build
                for build in build_list:
                    build_id = build.id
                    print(f"   Fetching logs for build: {build_id} (Status: {build.status.name})")
                    self.logger.info(f"Fetching logs for build: {build_id}")
                    
                    # Check if build has logs
                    if build.log_url:
                        print(f"   Build logs available at: {build.log_url}")
                        self.logger.info(f"Build logs URL: {build.log_url}")
                    
                    # Show build steps and their status
                    if build.steps:
                        print(f"\n🔍 Build Steps for {build_id}:")
                        print("=" * 60)
                        for i, step in enumerate(build.steps):
                            status = step.status.name if step.status else "UNKNOWN"
                            name = step.name or f"step-{i}"
                            print(f"   Step {i+1}: {name} - {status}")
                            
                            # Show failed step details
                            if step.status and step.status.name == "FAILURE":
                                if hasattr(step, 'args') and step.args:
                                    print(f"     Args: {' '.join(step.args[:3])}...")  # Show first few args
                        print("=" * 60)
                        break  # Only show the first build with steps
                    
            else:
                print("   No recent builds found")
                self.logger.warning("No recent builds found")
                
        except Exception as e:
            self.logger.error(f"Client library build log fetch error: {e}")
            raise
    
    def _fetch_build_logs_with_gcloud(self, service_name: str):
        """Fetch build logs using gcloud CLI (fallback method)"""
        try:
            print("\n📜 Fetching recent build logs for debugging...")
            
            # Get recent Cloud Build logs (get the 3 most recent builds)
            cmd = [
                'gcloud', 'builds', 'list',
                '--limit', '3',
                '--format', 'value(id)',
                '--project', self.project_id,
                '--sort-by', '~createTime'
            ]
            self.logger.debug(f"Running build list command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.logger.debug(f"Build list result - returncode: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                build_ids = result.stdout.strip().split('\n')
                print(f"   Found recent builds: {len(build_ids)}")
                self.logger.info(f"Found {len(build_ids)} recent builds: {build_ids}")
                
                # Get logs for the most recent build
                for build_id in build_ids:
                    if build_id.strip():
                        print(f"   Fetching logs for build: {build_id}")
                        self.logger.info(f"Fetching logs for build: {build_id}")
                        
                        # Get the build logs
                        log_cmd = [
                            'gcloud', 'builds', 'log', build_id.strip(),
                            '--project', self.project_id
                        ]
                        self.logger.debug(f"Running build log command: {' '.join(log_cmd)}")
                        
                        log_result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=60)
                        self.logger.debug(f"Build log result - returncode: {log_result.returncode}")
                        
                        if log_result.returncode == 0 and log_result.stdout:
                            sanitized_log = sanitize_secrets(log_result.stdout)
                            print(f"\n🔍 Build Log Details for {build_id}:")
                            print("=" * 60)
                            # Show last 50 lines of build log (sanitized)
                            lines = sanitized_log.strip().split('\n')
                            for line in lines[-50:]:
                                print(f"   {line}")
                            print("=" * 60)
                            
                            # Log the full build log (sanitized)
                            self.logger.error(f"FULL BUILD LOG FOR {build_id}:")
                            self.logger.error("=" * 40)
                            self.logger.error(sanitized_log)
                            self.logger.error("=" * 40)
                            break  # Only show the first successful log
                        else:
                            print(f"   Could not retrieve logs for build {build_id}")
                            self.logger.warning(f"Could not retrieve logs for build {build_id}")
            else:
                print("   No recent builds found")
                self.logger.warning("No recent builds found")
                
        except subprocess.TimeoutExpired:
            timeout_msg = "Timeout while fetching build logs"
            print(f"   {timeout_msg}")
            self.logger.error(timeout_msg)
        except Exception as e:
            error_msg = f"Could not fetch build logs: {e}"
            print(f"   {error_msg}")
            self.logger.error(error_msg)
            self.logger.error(f"Build log fetch exception: {traceback.format_exc()}")
    
    def _fetch_recent_build_logs(self):
        """Fetch most recent build logs as fallback"""
        try:
            print("   Checking most recent builds...")
            
            cmd = [
                'gcloud', 'builds', 'list',
                '--limit', '1',
                '--format', 'value(id)',
                '--project', self.project_id
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                build_id = result.stdout.strip()
                print(f"   Most recent build: {build_id}")
                
                # Get the build logs
                log_cmd = [
                    'gcloud', 'builds', 'log', build_id,
                    '--project', self.project_id
                ]
                
                log_result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=60)
                
                if log_result.returncode == 0 and log_result.stdout:
                    print("\n🔍 Most Recent Build Log (last 30 lines):")
                    print("=" * 60)
                    lines = log_result.stdout.strip().split('\n')
                    for line in lines[-30:]:
                        print(f"   {line}")
                    print("=" * 60)
            
        except Exception as e:
            print(f"   Could not fetch recent build logs: {e}")