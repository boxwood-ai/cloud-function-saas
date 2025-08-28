#!/usr/bin/env python3
"""
Cloud Function Microservice Generator Prototype
Transforms spec.md files into deployed Google Cloud Run functions

This is the main orchestrator that coordinates all the modular components:
- UI: Terminal interface and user feedback
- SpecParser: Parses markdown specification files  
- CodeGenerator: Generates Cloud Run function code using Claude AI
- CloudRunDeployer: Deploys functions to Google Cloud Run
- Utils: Shared utility functions for logging, validation, etc.
"""

import os
import sys
import json
import argparse
from datetime import datetime
import traceback

# Load environment variables
from dotenv import load_dotenv

# Import our modular components
from ui import FancyUI, TaskStatus
from spec_parser import SpecParser
from code_generator import CodeGenerator
from multi_agent_generator import MultiAgentCodeGenerator
from cloud_run_deployer import CloudRunDeployer
from utils import setup_logging, validate_configuration

load_dotenv()


def main():
    """Main prototype function - orchestrates the entire workflow"""
    parser = argparse.ArgumentParser(
        description='Cloud Function Microservice Generator Prototype',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python prototype.py spec.md                    # Use multi-agent generation (default)
  python prototype.py spec.md --single-agent     # Use classic single-agent mode
  python prototype.py spec.md --multi-agent      # Force multi-agent mode
  python prototype.py spec.md --project my-gcp   # Override GCP project
  python prototype.py spec.md --validate-only    # Only validate configuration
  python prototype.py spec.md --debug            # Enable debug output
  python prototype.py spec.md --debug --verbose  # Maximum debugging info
        """
    )
    parser.add_argument('spec_file', help='Path to spec.md file')
    parser.add_argument('--project', help='Google Cloud project ID (overrides .env)')
    parser.add_argument('--region', help='Deployment region (overrides .env)')
    parser.add_argument('--output-dir', help='Output directory (default: generated/timestamp-service)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate configuration, don\'t deploy')
    parser.add_argument('--dry-run', action='store_true', help='Generate files but don\'t deploy (show what would be deployed)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output to see what\'s happening')
    parser.add_argument('--multi-agent', action='store_true', help='Use multi-agent code generation (experimental)')
    parser.add_argument('--single-agent', action='store_true', help='Force single-agent code generation (classic mode)')
    
    args = parser.parse_args()
    
    # Initialize UI
    ui = FancyUI(use_rich=not getattr(args, 'simple_ui', False))
    
    # Setup main workflow tasks
    ui.add_task('validate', 'Validating configuration')
    ui.add_task('parse_spec', 'Parsing specification file')  
    ui.add_task('generate_code', 'Generating Cloud Run function code')
    ui.add_task('write_files', 'Writing generated files')
    ui.add_task('validate_files', 'Validating generated files')
    ui.add_task('deploy', 'Deploying to Google Cloud Run')
    
    # Step 1: Validate configuration
    ui.update_task('validate', TaskStatus.IN_PROGRESS)
    ui.print_status()
    
    with ui.spinner("Validating configuration"):
        errors, warnings = validate_configuration()
    
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
    print("✅ Configuration validated successfully!")
    
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
    except Exception as e:
        ui.update_task('parse_spec', TaskStatus.FAILED)
        print(f"\n❌ Error parsing spec file: {e}")
        sys.exit(1)
    
    # Step 3: Generate code
    ui.update_task('generate_code', TaskStatus.IN_PROGRESS)
    
    # Determine which code generation approach to use
    use_multi_agent = False
    if args.multi_agent:
        use_multi_agent = True
        print("\n🤖 Generating code with multi-agent system...")
    elif args.single_agent:
        use_multi_agent = False
        print("\n🤖 Generating code with single-agent system...")
    else:
        # Default: use multi-agent for better quality
        use_multi_agent = True
        print("\n🤖 Generating code with multi-agent system (default)...")
        if args.verbose:
            print("   💡 Use --single-agent to use classic generation mode")
    
    try:
        if use_multi_agent:
            # Use new multi-agent system
            multi_agent_generator = MultiAgentCodeGenerator(debug=args.debug)
            generated_files = multi_agent_generator.generate_cloud_function(spec)
        else:
            # Use classic single-agent system
            code_generator = CodeGenerator(debug=args.debug)
            generated_files = code_generator.generate_cloud_function(spec)
        
        if not generated_files:
            ui.update_task('generate_code', TaskStatus.FAILED)
            print("❌ Error: Failed to generate code")
            sys.exit(1)
        
        ui.update_task('generate_code', TaskStatus.COMPLETED)
        generation_mode = "multi-agent" if use_multi_agent else "single-agent"
        print(f"✅ Generated {len(generated_files)} files successfully ({generation_mode})")
        
        if args.verbose and generated_files:
            print("   📄 Generated files:")
            for filename in generated_files.keys():
                print(f"     • {filename}")
                
    except Exception as e:
        ui.update_task('generate_code', TaskStatus.FAILED)
        generation_mode = "multi-agent" if use_multi_agent else "single-agent"
        print(f"❌ Error generating code ({generation_mode}): {e}")
        
        # If multi-agent fails, try single-agent as fallback
        if use_multi_agent and not args.multi_agent:  # Only fallback if auto-selected multi-agent
            print("🔄 Falling back to single-agent generation...")
            try:
                code_generator = CodeGenerator(debug=args.debug)
                generated_files = code_generator.generate_cloud_function(spec)
                print(f"✅ Generated {len(generated_files)} files successfully (single-agent fallback)")
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                sys.exit(1)
        else:
            sys.exit(1)
    
    # Step 4: Create output directory and setup logging
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Create timestamped directory in generated folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        service_name_clean = (spec.name or 'unnamed').lower().replace(' ', '-').replace('_', '-')
        output_dir = os.path.join('generated', f'{timestamp}_{service_name_clean}')
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        if args.debug:
            print(f"🔍 Debug - Created output directory: {output_dir}")
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        sys.exit(1)
    
    # Setup logging now that we have the output directory
    logger = setup_logging(output_dir, args.debug)
    logger.info("Main execution started")
    logger.info(f"Arguments: spec_file={args.spec_file}, project={args.project}, region={args.region}, output_dir={args.output_dir}, debug={args.debug}")
    logger.info(f"Output directory: {output_dir}")
    
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
                logger.debug(f"File {filename} preview: {preview}")
        
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
        logger.error(f"File writing exception: {traceback.format_exc()}")
        if args.debug:
            print(f"🔍 Debug - Full traceback: {traceback.format_exc()}")
        sys.exit(1)
    
    # Step 6: Validate generated files
    ui.update_task('validate_files', TaskStatus.IN_PROGRESS)
    print("\n🔍 Validating generated files before deployment...")
    logger.info("Validating generated files before deployment...")
    
    required_files = ['package.json', 'index.js', 'Dockerfile']
    missing_files = []
    validation_errors = []
    
    for file in required_files:
        file_path = os.path.join(output_dir, file)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {file} ({file_size} bytes)")
            
            # Validate file contents
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if file == 'package.json':
                    # Validate JSON and check for required fields
                    try:
                        package_data = json.loads(content)
                        
                        # Check required fields
                        if 'main' not in package_data:
                            validation_errors.append(f"{file}: Missing 'main' field")
                        elif package_data['main'] != 'index.js':
                            validation_errors.append(f"{file}: 'main' should be 'index.js', got '{package_data['main']}'")
                        
                        if 'scripts' not in package_data or 'start' not in package_data.get('scripts', {}):
                            validation_errors.append(f"{file}: Missing 'start' script")
                        
                        if 'dependencies' not in package_data:
                            validation_errors.append(f"{file}: Missing 'dependencies' section")
                        elif 'express' not in package_data['dependencies']:
                            validation_errors.append(f"{file}: Missing 'express' dependency")
                        
                        print(f"      ✅ Valid JSON with required fields")
                        
                    except json.JSONDecodeError as e:
                        validation_errors.append(f"{file}: Invalid JSON - {e}")
                        print(f"      ❌ Invalid JSON")
                
                elif file == 'index.js':
                    # Check for basic Node.js/Express patterns
                    if 'express' not in content:
                        validation_errors.append(f"{file}: Missing Express.js import")
                    if 'app.listen' not in content and 'listen(' not in content:
                        validation_errors.append(f"{file}: Missing server listen call")
                    if 'process.env.PORT' not in content:
                        validation_errors.append(f"{file}: Missing PORT environment variable usage")
                    
                    if not validation_errors or not any(file in error for error in validation_errors):
                        print(f"      ✅ Contains Express.js server code")
                
                elif file == 'Dockerfile':
                    # Check for critical Docker/Cloud Run requirements
                    dockerfile_checks = [
                        ('EXPOSE 8080', 'Missing EXPOSE 8080 directive (required for Cloud Run)'),
                        ('FROM node:', 'Missing Node.js base image'),
                        ('CMD ', 'Missing CMD directive'),
                        ('WORKDIR ', 'Missing WORKDIR directive'),
                    ]
                    
                    dockerfile_errors = []
                    for check, error_msg in dockerfile_checks:
                        if check not in content:
                            dockerfile_errors.append(f"{file}: {error_msg}")
                            validation_errors.append(f"{file}: {error_msg}")
                    
                    if not dockerfile_errors:
                        print(f"      ✅ Contains required Cloud Run directives")
                    else:
                        print(f"      ❌ Missing critical directives: {len(dockerfile_errors)}")
                        for error in dockerfile_errors:
                            print(f"        • {error.split(': ', 1)[1]}")
                
            except Exception as e:
                validation_errors.append(f"{file}: Could not validate content - {e}")
                print(f"      ⚠️ Could not validate content")
        else:
            missing_files.append(file)
            print(f"   ❌ {file} - MISSING")
    
    # Show validation results
    if missing_files:
        ui.update_task('validate_files', TaskStatus.FAILED)
        print(f"\n❌ Cannot deploy: Missing required files: {', '.join(missing_files)}")
        sys.exit(1)
    
    if validation_errors:
        ui.update_task('validate_files', TaskStatus.WARNING)
        print(f"\n⚠️ Validation warnings found:")
        for error in validation_errors:
            print(f"   • {error}")
        print(f"\n💡 These issues might cause build failures. Continuing with deployment...")
    else:
        ui.update_task('validate_files', TaskStatus.COMPLETED)
        print(f"\n✅ All files validated successfully!")
    
    # Step 7: Deploy to Cloud Run
    ui.update_task('deploy', TaskStatus.IN_PROGRESS)
    print("\n🚀 Preparing for Google Cloud Run deployment...")
    
    service_name = spec.name.lower().replace(' ', '-').replace('_', '-')
    logger.info(f"Preparing deployment for service: {service_name}")
    deployer = CloudRunDeployer(args.project, args.region, logger)
    
    if not deployer.project_id:
        ui.update_task('deploy', TaskStatus.FAILED)
        error_msg = "No Google Cloud project specified. Use --project or set GOOGLE_CLOUD_PROJECT in .env"
        print(f"❌ Error: {error_msg}")
        logger.error(error_msg)
        sys.exit(1)
    
    print("\n📋 Deployment configuration:")
    print(f"   • Service name: {service_name}")
    print(f"   • Project ID: {deployer.project_id}")
    print(f"   • Region: {deployer.region}")
    print(f"   • Source directory: {output_dir}")
    
    if args.debug:
        print(f"\n🔍 Debug - Full gcloud command will be:")
        print(f"   gcloud run deploy {service_name} --source {output_dir} --platform managed --region {deployer.region} --allow-unauthenticated")
    
    # Exit if dry-run mode
    if args.dry_run:
        print("\n🏃 Dry run mode - deployment skipped")
        print("✅ All files generated and validated successfully!")
        print(f"💡 To deploy manually, run:")
        print(f"   gcloud run deploy {service_name} --source {output_dir} --platform managed --region {deployer.region} --allow-unauthenticated")
        ui.update_task('deploy', TaskStatus.COMPLETED)
        ui.print_status()
        return
    
    try:
        logger.info("Starting deployment process...")
        print("\n🔄 Starting deployment to Google Cloud Run...")
        print("   This may take several minutes as Cloud Run builds and deploys your service...")
        
        if args.debug:
            # In debug mode, don't use spinner so we can see real-time output
            print("🔍 Debug mode: Running deployment without spinner for detailed output...")
            success = deployer.deploy(service_name, output_dir)
        else:
            with ui.spinner("Deploying to Google Cloud Run"):
                success = deployer.deploy(service_name, output_dir)
        
        if success:
            ui.update_task('deploy', TaskStatus.COMPLETED)
            success_msg = f"Successfully deployed {spec.name} to Cloud Run!"
            print(f"\n🎉 {success_msg}")
            logger.info(success_msg)
            
            service_url = f"https://{service_name}-{deployer.project_id}.{deployer.region}.run.app"
            print(f"\n🌐 Service URL: {service_url}")
            print(f"\n📊 Deployment Summary:")
            print(f"   • Service: {service_name}")
            print(f"   • URL: {service_url}")
            print(f"   • Region: {deployer.region}")
            print(f"   • Project: {deployer.project_id}")
            
            logger.info(f"Deployment successful - Service URL: {service_url}")
            logger.info(f"Final deployment summary - Service: {service_name}, Region: {deployer.region}, Project: {deployer.project_id}")
            
            if args.verbose:
                print("\n💡 Next steps:")
                print(f"   • Test health check: curl {service_url}")
                print(f"   • View logs: gcloud logs read --service={service_name} --project={deployer.project_id}")
                print(f"   • Monitor service: https://console.cloud.google.com/run/detail/{deployer.region}/{service_name}/overview?project={deployer.project_id}")
                print(f"   • Update service: gcloud run deploy {service_name} --source {output_dir} --region {deployer.region}")
        else:
            ui.update_task('deploy', TaskStatus.FAILED)
            failure_msg = "Deployment failed"
            print(f"\n❌ {failure_msg}")
            print(f"💡 Generated files are available at: {output_dir}")
            print(f"💡 You can deploy manually with: gcloud run deploy {service_name} --source {output_dir} --region {deployer.region}")
            logger.error(failure_msg)
            logger.info(f"Manual deployment command: gcloud run deploy {service_name} --source {output_dir} --region {deployer.region}")
    except Exception as e:
        ui.update_task('deploy', TaskStatus.FAILED)
        error_msg = f"Deployment error: {e}"
        print(f"❌ {error_msg}")
        print(f"💡 Generated files are available at: {output_dir}")
        logger.error(error_msg)
        logger.error(f"Deployment exception: {traceback.format_exc()}")
        sys.exit(1)
    
    # Show final status
    ui.print_status()
    
    # Keep generated files (cleanup disabled)
    print(f"📁 Generated files preserved at: {output_dir}")
    logger.info("Session completed successfully")
    logger.info("=" * 60)
    print(f"📝 Debug log saved at: {os.path.join(output_dir, 'generation.log')}")


if __name__ == '__main__':
    main()