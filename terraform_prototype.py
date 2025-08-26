#!/usr/bin/env python3
"""
Terraform-Powered Cloud Function Microservice Generator
Transforms spec.md files into multi-cloud deployments using Terraform

This is the enhanced orchestrator that supports multi-cloud deployments:
- UI: Terminal interface and user feedback
- SpecParser: Parses markdown specification files  
- TerraformCodeGenerator: Generates application code + Terraform configs using Claude AI
- TerraformDeployer: Deploys using Terraform to multiple cloud providers
- Utils: Shared utility functions for logging, validation, etc.
"""

import os
import sys
import json
import argparse
from datetime import datetime
import traceback
from typing import List

# Load environment variables
from dotenv import load_dotenv

# Import our modular components
from ui import FancyUI, TaskStatus
from spec_parser import SpecParser
from terraform_code_generator import TerraformCodeGenerator
from terraform_deployer import TerraformDeployer
from terraform_validator import TerraformValidator
from utils import setup_logging, validate_configuration

load_dotenv()


def parse_providers(provider_arg: str) -> List[str]:
    """Parse provider argument into list of valid providers"""
    if not provider_arg:
        return ['gcp']  # Default to GCP
    
    # Handle comma-separated providers
    providers = [p.strip().lower() for p in provider_arg.split(',')]
    
    # Handle special cases first
    if 'both' in providers:
        return ['gcp', 'aws']
    
    # Validate providers
    valid_providers = ['gcp', 'aws', 'azure']
    invalid_providers = [p for p in providers if p not in valid_providers]
    
    if invalid_providers:
        print(f"❌ Error: Invalid providers: {', '.join(invalid_providers)}")
        print(f"💡 Valid providers are: {', '.join(valid_providers)}")
        sys.exit(1)
    
    return list(set(providers))  # Remove duplicates


def validate_provider_prerequisites(providers: List[str]) -> List[str]:
    """Validate that required tools and authentication are available for each provider"""
    errors = []
    
    for provider in providers:
        if provider == 'gcp':
            # Check gcloud CLI
            if not os.system('gcloud version > /dev/null 2>&1') == 0:
                errors.append("GCP: gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install")
            
            # Check authentication
            if not os.system('gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1') == 0:
                errors.append("GCP: Not authenticated. Run: gcloud auth login")
        
        elif provider == 'aws':
            # Check AWS CLI
            if not os.system('aws --version > /dev/null 2>&1') == 0:
                errors.append("AWS: AWS CLI not found. Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
            
            # Check authentication
            if not os.system('aws sts get-caller-identity > /dev/null 2>&1') == 0:
                errors.append("AWS: Not authenticated. Run: aws configure")
        
        elif provider == 'azure':
            # Check Azure CLI
            if not os.system('az version > /dev/null 2>&1') == 0:
                errors.append("Azure: Azure CLI not found. Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
            
            # Check authentication
            if not os.system('az account show > /dev/null 2>&1') == 0:
                errors.append("Azure: Not authenticated. Run: az login")
    
    return errors


def main():
    """Main terraform prototype function - orchestrates the entire multi-cloud workflow"""
    parser = argparse.ArgumentParser(
        description='Terraform-Powered Cloud Function Microservice Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python terraform_prototype.py spec.md                           # Deploy to GCP (default)
  python terraform_prototype.py spec.md --provider gcp            # Deploy to GCP only
  python terraform_prototype.py spec.md --provider aws            # Deploy to AWS only
  python terraform_prototype.py spec.md --provider gcp,aws        # Deploy to both GCP and AWS
  python terraform_prototype.py spec.md --provider both           # Deploy to both GCP and AWS
  python terraform_prototype.py spec.md --legacy                  # Use legacy CloudRun deployment
  python terraform_prototype.py spec.md --validate-only           # Only validate configuration
  python terraform_prototype.py spec.md --terraform-plan-only     # Generate and plan, don't deploy
        """
    )
    
    parser.add_argument('spec_file', help='Path to spec.md file')
    
    # Cloud Provider Options
    parser.add_argument('--provider', '-p', 
                       help='Cloud provider(s): gcp, aws, azure, both, or comma-separated list (default: gcp)')
    
    # Terraform Options
    parser.add_argument('--terraform-plan-only', action='store_true',
                       help='Generate files and create Terraform plan, but don\'t apply')
    parser.add_argument('--terraform-destroy', action='store_true',
                       help='Destroy existing Terraform-managed infrastructure')
    parser.add_argument('--terraform-workspace',
                       help='Terraform workspace to use (default: default)')
    parser.add_argument('--terraform-var-file',
                       help='Terraform variables file to use')
    
    # Container Options
    parser.add_argument('--container-image',
                       help='Override container image URL (skips build step)')
    parser.add_argument('--skip-container-build', action='store_true',
                       help='Skip container build and use existing image')
    parser.add_argument('--force-rebuild', action='store_true',
                       help='Force rebuild of container (no cache)')
    
    # Legacy Options
    parser.add_argument('--legacy', action='store_true',
                       help='Use legacy CloudRun deployment instead of Terraform')
    
    # Existing Options
    parser.add_argument('--project', help='Google Cloud project ID (overrides .env)')
    parser.add_argument('--region', help='Deployment region (overrides .env)')
    parser.add_argument('--output-dir', help='Output directory (default: generated/timestamp-service)')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate configuration, don\'t deploy')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Generate files but don\'t deploy (show what would be deployed)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Parse providers
    providers = parse_providers(args.provider)
    
    # Initialize UI
    ui = FancyUI(use_rich=not getattr(args, 'simple_ui', False))
    
    print(f"🚀 Cloud Function SaaS - Terraform Multi-Cloud Edition")
    print(f"Target Provider(s): {', '.join(providers).upper()}")
    if args.legacy:
        print("🔧 Using legacy CloudRun deployment")
    
    # Handle Terraform destroy
    if args.terraform_destroy:
        if args.output_dir and os.path.exists(args.output_dir):
            print(f"\n💥 Destroying infrastructure in: {args.output_dir}")
            deployer = TerraformDeployer(args.output_dir)
            success = deployer.destroy_deployment(
                var_file=args.terraform_var_file,
                auto_approve=not args.debug  # Require manual approval in debug mode
            )
            if success:
                print("✅ Infrastructure destroyed successfully!")
            else:
                print("❌ Failed to destroy infrastructure")
                sys.exit(1)
            return
        else:
            print("❌ Error: --output-dir required for --terraform-destroy")
            sys.exit(1)
    
    # Setup workflow tasks
    if args.legacy:
        # Legacy workflow tasks
        ui.add_task('validate', 'Validating configuration')
        ui.add_task('parse_spec', 'Parsing specification file')
        ui.add_task('generate_code', 'Generating Cloud Run function code')
        ui.add_task('write_files', 'Writing generated files')
        ui.add_task('validate_files', 'Validating generated files')
        ui.add_task('deploy', 'Deploying to Google Cloud Run')
    else:
        # Terraform workflow tasks
        ui.add_task('validate', 'Validating configuration and prerequisites')
        ui.add_task('parse_spec', 'Parsing specification file')
        ui.add_task('generate_terraform', 'Generating application code and Terraform configuration')
        ui.add_task('write_files', 'Writing generated files')
        ui.add_task('validate_terraform', 'Validating Terraform configuration')
        if not args.terraform_plan_only:
            ui.add_task('deploy_terraform', 'Deploying with Terraform')
        else:
            ui.add_task('plan_terraform', 'Creating Terraform execution plan')
    
    # Step 1: Validate configuration and prerequisites
    ui.update_task('validate', TaskStatus.IN_PROGRESS)
    ui.print_status()
    
    with ui.spinner("Validating configuration and prerequisites"):
        # Basic configuration validation
        errors, warnings = validate_configuration()
        
        # Provider-specific prerequisite validation
        if not args.legacy:
            provider_errors = validate_provider_prerequisites(providers)
            errors.extend(provider_errors)
    
    # Show warnings
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   • {warning}")
    
    # Show errors and exit if any
    if errors:
        ui.update_task('validate', TaskStatus.FAILED)
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"   • {error}")
        print("\n💡 Please fix the above errors and try again.")
        sys.exit(1)
    
    ui.update_task('validate', TaskStatus.COMPLETED)
    print("✅ Configuration and prerequisites validated successfully!")
    
    # Exit if only validating
    if args.validate_only:
        print("\n🎉 All checks passed! Ready to generate and deploy microservices.")
        return
    
    # Step 2: Parse specification file
    ui.update_task('parse_spec', TaskStatus.IN_PROGRESS)
    
    # Check if spec file exists
    if not os.path.exists(args.spec_file):
        ui.update_task('parse_spec', TaskStatus.FAILED)
        print(f"\n❌ Error: Spec file '{args.spec_file}' not found")
        print("💡 Make sure the file path is correct or create the spec file first.")
        sys.exit(1)
    
    # Read and parse spec
    print(f"\n📖 Reading spec from {args.spec_file}...")
    
    try:
        with open(args.spec_file, 'r') as f:
            spec_content = f.read()
        if not spec_content.strip():
            ui.update_task('parse_spec', TaskStatus.FAILED)
            print(f"\n❌ Error: Spec file '{args.spec_file}' is empty")
            sys.exit(1)
    except Exception as e:
        ui.update_task('parse_spec', TaskStatus.FAILED)
        print(f"\n❌ Error reading spec file: {e}")
        sys.exit(1)
    
    spec_parser = SpecParser()
    try:
        spec = spec_parser.parse(spec_content)
        if not spec.name:
            print("⚠️  Warning: No service name found in spec")
        if not spec.endpoints:
            print("⚠️  Warning: No endpoints defined in spec")
        
        ui.update_task('parse_spec', TaskStatus.COMPLETED)
        print(f"✅ Parsed spec for service: {spec.name or 'Unnamed Service'}")
        
        if args.verbose:
            print(f"   • Description: {spec.description}")
            print(f"   • Runtime: {spec.runtime}")
            print(f"   • Endpoints: {len(spec.endpoints)}")
            print(f"   • Models: {len(spec.models)}")
            print(f"   • Target Providers: {', '.join(providers)}")
    except Exception as e:
        ui.update_task('parse_spec', TaskStatus.FAILED)
        print(f"\n❌ Error parsing spec file: {e}")
        sys.exit(1)
    
    # Step 3: Create output directory and setup logging (moved earlier)
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Create timestamped directory in generated folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        service_name_clean = (spec.name or 'unnamed').lower().replace(' ', '-').replace('_', '-')
        provider_suffix = '-'.join(providers) if len(providers) > 1 else providers[0]
        output_dir = os.path.join('generated', f'{timestamp}_{service_name_clean}_{provider_suffix}')
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        if args.debug:
            print(f"🔍 Debug - Created output directory: {output_dir}")
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        sys.exit(1)
    
    # Setup logging now that we have the output directory
    logger = setup_logging(output_dir, args.debug)
    logger.info("Terraform deployment session started")
    logger.info(f"Arguments: spec_file={args.spec_file}, providers={providers}, output_dir={args.output_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Step 4: Generate code and Terraform configuration
    if args.legacy:
        # Use legacy code generation
        from code_generator import CodeGenerator
        ui.update_task('generate_code', TaskStatus.IN_PROGRESS)
        print("\n🤖 Generating Cloud Run function code with Claude...")
        
        code_generator = CodeGenerator(debug=args.debug)
        try:
            generated_files = code_generator.generate_cloud_function(spec)
            if not generated_files:
                ui.update_task('generate_code', TaskStatus.FAILED)
                print("❌ Error: Failed to generate code")
                sys.exit(1)
            ui.update_task('generate_code', TaskStatus.COMPLETED)
            print(f"✅ Generated {len(generated_files)} files successfully")
        except Exception as e:
            ui.update_task('generate_code', TaskStatus.FAILED)
            print(f"❌ Error generating code: {e}")
            sys.exit(1)
    else:
        # Use Terraform-powered code generation
        ui.update_task('generate_terraform', TaskStatus.IN_PROGRESS)
        print(f"\n🤖 Generating application code and Terraform configuration with Claude...")
        print(f"   Target providers: {', '.join(providers)}")
        
        terraform_generator = TerraformCodeGenerator(debug=args.debug)
        try:
            generated_files = terraform_generator.generate_multi_cloud_deployment(spec, providers)
            if not generated_files:
                ui.update_task('generate_terraform', TaskStatus.FAILED)
                print("❌ Error: Failed to generate Terraform configuration")
                sys.exit(1)
            
            # Add README for deployment instructions
            readme_content = terraform_generator.generate_deployment_readme(spec, providers)
            generated_files['README-DEPLOYMENT.md'] = readme_content
            
            print(f"✅ Generated {len(generated_files)} files initially")
            
            # Validate and auto-fix generated files
            print("🔍 Validating and auto-fixing generated Terraform configuration...")
            validator = TerraformValidator(logger)
            validation_success, fixed_files = validator.validate_and_fix(
                generated_files, spec, providers, output_dir, max_retries=3
            )
            
            if not validation_success:
                ui.update_task('generate_terraform', TaskStatus.FAILED)
                print("❌ Error: Failed to generate valid Terraform configuration after auto-fix attempts")
                print("💡 Generated files have been saved, but may require manual fixes")
            else:
                generated_files = fixed_files
                ui.update_task('generate_terraform', TaskStatus.COMPLETED)
                print(f"✅ Generated and validated {len(generated_files)} files successfully")
            
            if args.verbose:
                terraform_files = [f for f in generated_files.keys() if f.endswith('.tf') or f.endswith('.tfvars')]
                app_files = [f for f in generated_files.keys() if not (f.endswith('.tf') or f.endswith('.tfvars') or f.endswith('.md'))]
                print(f"   • Application files: {len(app_files)}")
                print(f"   • Terraform files: {len(terraform_files)}")
                
        except Exception as e:
            ui.update_task('generate_terraform', TaskStatus.FAILED)
            print(f"❌ Error generating Terraform configuration: {e}")
            sys.exit(1)
    
    # Step 5: Write generated files
    ui.update_task('write_files', TaskStatus.IN_PROGRESS)
    logger.info("Writing generated files...")
    print(f"\n📝 Writing generated files to {output_dir}...")
    
    try:
        file_count = 0
        total_size = 0
        
        for filename, content in generated_files.items():
            file_path = os.path.join(output_dir, filename)
            logger.debug(f"Writing file: {filename} ({len(content)} bytes)")
            
            # Create subdirectories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            file_size = len(content)
            total_size += file_size
            file_count += 1
            
            print(f"   ✅ Created: {filename} ({file_size} bytes)")
            logger.info(f"Created file: {filename} ({file_size} bytes)")
            
            if args.verbose:
                # Show first few lines of each file for verification
                preview_lines = content.split('\n')[:3]
                preview = f"{preview_lines[0][:60]}{'...' if len(preview_lines[0]) > 60 else ''}"
                print(f"      Preview: {preview}")
        
        ui.update_task('write_files', TaskStatus.COMPLETED)
        print(f"\n📊 File generation summary:")
        print(f"   • Files created: {file_count}")
        print(f"   • Total size: {total_size} bytes")
        print(f"   • Output directory: {output_dir}")
        
        logger.info(f"File generation complete - {file_count} files, {total_size} bytes total")
        
    except Exception as e:
        ui.update_task('write_files', TaskStatus.FAILED)
        error_msg = f"Error writing files: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        if args.debug:
            print(f"🔍 Debug - Full traceback: {traceback.format_exc()}")
        sys.exit(1)
    
    # Step 6: Validate generated files (different for Terraform vs Legacy)
    if args.legacy:
        # Legacy validation (existing logic)
        ui.update_task('validate_files', TaskStatus.IN_PROGRESS)
        # ... existing validation logic ...
        ui.update_task('validate_files', TaskStatus.COMPLETED)
    else:
        # Terraform validation
        ui.update_task('validate_terraform', TaskStatus.IN_PROGRESS)
        print("\n🔍 Validating Terraform configuration...")
        logger.info("Validating Terraform configuration...")
        
        deployer = TerraformDeployer(output_dir, logger)
        
        try:
            # Check Terraform version
            tf_version = deployer.check_terraform_version()
            if tf_version:
                print(f"   ✅ Terraform version: {tf_version}")
            else:
                print(f"   ⚠️ Could not determine Terraform version")
            
            # Initialize Terraform first to install modules
            print("   🔄 Initializing Terraform...")
            if not deployer.init_terraform():
                ui.update_task('validate_terraform', TaskStatus.FAILED)
                print("❌ Terraform initialization failed")
                sys.exit(1)
            
            print("   ✅ Terraform initialized successfully")
            
            # Now validate Terraform files
            valid, validation_errors = deployer.validate_terraform_files()
            if not valid:
                ui.update_task('validate_terraform', TaskStatus.FAILED)
                print("❌ Terraform validation failed:")
                for error in validation_errors:
                    print(f"   • {error}")
                sys.exit(1)
            
            ui.update_task('validate_terraform', TaskStatus.COMPLETED)
            print("✅ Terraform configuration validated successfully!")
            
        except Exception as e:
            ui.update_task('validate_terraform', TaskStatus.FAILED)
            error_msg = f"Terraform validation error: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            sys.exit(1)
    
    # Step 7: Deploy or Plan
    if args.legacy:
        # Use existing legacy deployment logic
        from cloud_run_deployer import CloudRunDeployer
        ui.update_task('deploy', TaskStatus.IN_PROGRESS)
        # ... existing legacy deployment logic ...
        ui.update_task('deploy', TaskStatus.COMPLETED)
    else:
        # Terraform deployment
        if args.terraform_plan_only:
            ui.update_task('plan_terraform', TaskStatus.IN_PROGRESS)
            print(f"\n📋 Creating Terraform execution plan...")
            
            try:
                # Initialize Terraform
                if not deployer.init_terraform():
                    ui.update_task('plan_terraform', TaskStatus.FAILED)
                    print("❌ Terraform initialization failed")
                    sys.exit(1)
                
                # Create plan - use the generated tfvars file
                tfvars_file = args.terraform_var_file
                if not tfvars_file:
                    # Auto-detect the provider-specific tfvars file
                    if len(providers) == 1:
                        tfvars_file = f'terraform-{providers[0]}.tfvars'
                    
                plan_success, plan_output = deployer.plan_deployment(
                    var_file=tfvars_file
                )
                
                if plan_success:
                    ui.update_task('plan_terraform', TaskStatus.COMPLETED)
                    print("✅ Terraform plan created successfully!")
                    print(f"\n📋 Plan Summary:")
                    print("   Run 'terraform apply' in the output directory to deploy")
                else:
                    ui.update_task('plan_terraform', TaskStatus.FAILED)
                    print(f"❌ Terraform plan failed: {plan_output}")
                    sys.exit(1)
                    
            except Exception as e:
                ui.update_task('plan_terraform', TaskStatus.FAILED)
                error_msg = f"Terraform planning error: {e}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
        else:
            ui.update_task('deploy_terraform', TaskStatus.IN_PROGRESS)
            print(f"\n🚀 Deploying to {', '.join(providers).upper()} with Terraform...")
            
            service_name = spec.name.lower().replace(' ', '-').replace('_', '-')
            logger.info(f"Starting Terraform deployment for service: {service_name}")
            
            try:
                # Handle workspace selection
                if args.terraform_workspace:
                    if not deployer.workspace_select(args.terraform_workspace):
                        print(f"❌ Failed to select workspace: {args.terraform_workspace}")
                        sys.exit(1)
                
                # Exit if dry-run mode
                if args.dry_run:
                    print("\n🏃 Dry run mode - deployment skipped")
                    print("✅ All files generated and validated successfully!")
                    print(f"💡 To deploy, run: cd {output_dir} && terraform apply")
                    ui.update_task('deploy_terraform', TaskStatus.COMPLETED)
                    ui.print_status()
                    return
                
                # Build and push container (unless overridden)
                container_image = None
                if args.container_image:
                    # Use provided container image
                    container_image = args.container_image
                    print(f"🐳 Using provided container image: {container_image}")
                    logger.info(f"Using manual container image override: {container_image}")
                elif not args.skip_container_build:
                    # Build and push container
                    from container_builder import ContainerBuilder
                    
                    print("🐳 Building and pushing container...")
                    builder = ContainerBuilder(output_dir, logger)
                    
                    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
                    region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
                    
                    if not project_id:
                        print("❌ GOOGLE_CLOUD_PROJECT not set in environment")
                        sys.exit(1)
                    
                    # Generate timestamp tag for unique builds
                    tag = builder.get_build_timestamp_tag()
                    
                    build_success, build_result = builder.build_and_push(
                        service_name=service_name,
                        project_id=project_id,
                        region=region,
                        tag=tag,
                        force_rebuild=args.force_rebuild
                    )
                    
                    if build_success:
                        container_image = build_result
                        print(f"✅ Container built and pushed: {container_image}")
                        logger.info(f"Container build successful: {container_image}")
                    else:
                        print(f"❌ Container build failed: {build_result}")
                        print("💡 You can skip container build with --skip-container-build")
                        print("💡 Or provide existing image with --container-image")
                        logger.error(f"Container build failed: {build_result}")
                        sys.exit(1)
                
                # Update terraform variables with actual container image
                if container_image:
                    # Update the tfvars file with the built container image
                    tfvars_path = os.path.join(output_dir, 'terraform-gcp.tfvars')
                    if os.path.exists(tfvars_path):
                        with open(tfvars_path, 'r') as f:
                            tfvars_content = f.read()
                        
                        # Replace container_image line
                        import re
                        updated_content = re.sub(
                            r'container_image = "[^"]*"',
                            f'container_image = "{container_image}"',
                            tfvars_content
                        )
                        
                        with open(tfvars_path, 'w') as f:
                            f.write(updated_content)
                        
                        logger.info(f"Updated {tfvars_path} with container image: {container_image}")
                
                # Deploy with Terraform
                # Use generated tfvars file if no custom one specified
                tfvars_file = args.terraform_var_file
                if not tfvars_file:
                    # Default to the generated provider-specific tfvars file
                    for provider in providers:
                        generated_tfvars_path = os.path.join(output_dir, f'terraform-{provider}.tfvars')
                        if os.path.exists(generated_tfvars_path):
                            # Use just the filename since terraform runs from the output directory
                            tfvars_file = f'terraform-{provider}.tfvars'
                            logger.info(f"Using generated tfvars file: {tfvars_file} (full path: {generated_tfvars_path})")
                            break
                
                if args.debug:
                    print("🔍 Debug mode: Running Terraform deployment with detailed output...")
                    success, outputs = deployer.deploy(
                        service_name, 
                        providers, 
                        var_file=tfvars_file,
                        auto_approve=False  # Require manual approval in debug mode
                    )
                else:
                    with ui.spinner("Deploying with Terraform (this may take several minutes)"):
                        success, outputs = deployer.deploy(
                            service_name, 
                            providers, 
                            var_file=tfvars_file,
                            auto_approve=True
                        )
                
                if success:
                    ui.update_task('deploy_terraform', TaskStatus.COMPLETED)
                    print(f"\n🎉 Successfully deployed {spec.name} to {', '.join(providers).upper()}!")
                    
                    # Display service URLs and important info
                    if outputs:
                        print(f"\n📊 Deployment Summary:")
                        
                        for provider in providers:
                            if provider == 'gcp' and 'gcp_service_url' in outputs:
                                print(f"   🌐 GCP Service URL: {outputs['gcp_service_url']}")
                            elif provider == 'aws' and 'aws_service_url' in outputs:
                                print(f"   🌐 AWS Service URL: {outputs['aws_service_url']}")
                        
                        # Show generic service URL if available
                        if 'service_url' in outputs:
                            print(f"   🌐 Service URL: {outputs['service_url']}")
                    
                    if args.verbose:
                        print(f"\n💡 Next steps:")
                        if 'service_url' in outputs:
                            print(f"   • Test service: curl {outputs['service_url']}/health")
                        print(f"   • View resources: cd {output_dir} && terraform show")
                        print(f"   • Update service: cd {output_dir} && terraform apply")
                        print(f"   • Destroy service: cd {output_dir} && terraform destroy")
                    
                else:
                    ui.update_task('deploy_terraform', TaskStatus.FAILED)
                    print("❌ Terraform deployment failed")
                    print(f"💡 Check logs in: {output_dir}")
                    print(f"💡 Manual deployment: cd {output_dir} && terraform apply")
                    sys.exit(1)
                    
            except Exception as e:
                ui.update_task('deploy_terraform', TaskStatus.FAILED)
                error_msg = f"Terraform deployment error: {e}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)
                logger.error(f"Deployment exception: {traceback.format_exc()}")
                sys.exit(1)
    
    # Show final status
    ui.print_status()
    
    # Keep generated files
    print(f"\n📁 Generated files preserved at: {output_dir}")
    logger.info("Session completed successfully")
    logger.info("=" * 60)
    print(f"📝 Debug log saved at: {os.path.join(output_dir, 'generation.log')}")


if __name__ == '__main__':
    main()