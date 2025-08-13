"""
Command-line interface for the Cloud Function SaaS Generator.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from .core.parser import SpecParser
from .core.generator import CodeGenerator
from .providers.base import ProviderFactory
from .providers import gcp  # Register GCP provider
from .utils.security import is_safe_project_id, is_safe_service_name


def setup_logging(debug: bool = False) -> logging.Logger:
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('cloud-function-saas')


def validate_environment() -> list[str]:
    """Validate required environment variables and tools"""
    errors = []
    
    # Check for AI API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        errors.append("ANTHROPIC_API_KEY environment variable is required")
    
    return errors


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Generate and deploy cloud functions from markdown specifications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate code only
  cloud-function-saas generate my-service.md
  
  # Generate and deploy to Google Cloud Run
  cloud-function-saas deploy my-service.md --provider gcp --project my-project
  
  # List deployed services
  cloud-function-saas list --provider gcp --project my-project
  
  # Get service logs
  cloud-function-saas logs my-service --provider gcp --project my-project
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate code from specification')
    generate_parser.add_argument('spec_file', help='Path to specification file (.md)')
    generate_parser.add_argument('--output', '-o', help='Output directory')
    generate_parser.add_argument('--runtime', default='nodejs', choices=['nodejs', 'python'], help='Runtime environment')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Generate and deploy service')
    deploy_parser.add_argument('spec_file', help='Path to specification file (.md)')
    deploy_parser.add_argument('--provider', required=True, choices=ProviderFactory.list_providers(), help='Cloud provider')
    deploy_parser.add_argument('--project', required=True, help='Cloud project ID')
    deploy_parser.add_argument('--region', help='Deployment region')
    deploy_parser.add_argument('--runtime', default='nodejs', choices=['nodejs', 'python'], help='Runtime environment')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List deployed services')
    list_parser.add_argument('--provider', required=True, choices=ProviderFactory.list_providers(), help='Cloud provider')
    list_parser.add_argument('--project', required=True, help='Cloud project ID')
    list_parser.add_argument('--region', help='Cloud region')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Get service logs')
    logs_parser.add_argument('service_name', help='Service name')
    logs_parser.add_argument('--provider', required=True, choices=ProviderFactory.list_providers(), help='Cloud provider')
    logs_parser.add_argument('--project', required=True, help='Cloud project ID')
    logs_parser.add_argument('--region', help='Cloud region')
    logs_parser.add_argument('--limit', type=int, default=100, help='Number of log entries')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete deployed service')
    delete_parser.add_argument('service_name', help='Service name')
    delete_parser.add_argument('--provider', required=True, choices=ProviderFactory.list_providers(), help='Cloud provider')
    delete_parser.add_argument('--project', required=True, help='Cloud project ID')
    delete_parser.add_argument('--region', help='Cloud region')
    delete_parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    
    # Global options
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging(args.debug)
    
    # Validate environment
    env_errors = validate_environment()
    if env_errors:
        logger.error("Environment validation failed:")
        for error in env_errors:
            logger.error(f"  • {error}")
        sys.exit(1)
    
    try:
        if args.command == 'generate':
            handle_generate(args, logger)
        elif args.command == 'deploy':
            handle_deploy(args, logger)
        elif args.command == 'list':
            handle_list(args, logger)
        elif args.command == 'logs':
            handle_logs(args, logger)
        elif args.command == 'delete':
            handle_delete(args, logger)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        if args.debug:
            import traceback
            logger.debug(traceback.format_exc())
        sys.exit(1)


def handle_generate(args, logger):
    """Handle the generate command"""
    logger.info(f"Generating code from {args.spec_file}")
    
    # Read and parse specification
    try:
        with open(args.spec_file, 'r') as f:
            spec_content = f.read()
    except FileNotFoundError:
        logger.error(f"Specification file not found: {args.spec_file}")
        sys.exit(1)
    
    parser = SpecParser()
    spec = parser.parse(spec_content)
    
    # Validate specification
    validation_errors = parser.validate_spec(spec)
    if validation_errors:
        logger.error("Specification validation failed:")
        for error in validation_errors:
            logger.error(f"  • {error}")
        sys.exit(1)
    
    # Generate code
    generator = CodeGenerator(debug=args.debug)
    files = generator.generate_cloud_function(spec, args.runtime)
    
    # Write files
    output_dir = args.output or f"generated/{spec.name.lower().replace(' ', '-')}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for filename, content in files.items():
        file_path = Path(output_dir) / filename
        file_path.write_text(content)
        logger.info(f"Created: {file_path}")
    
    logger.info(f"Code generated successfully in {output_dir}")


def handle_deploy(args, logger):
    """Handle the deploy command"""
    # Validate inputs
    if not is_safe_project_id(args.project):
        logger.error(f"Invalid project ID format: {args.project}")
        sys.exit(1)
    
    # First generate the code
    logger.info("Generating code...")
    
    # Read and parse specification
    with open(args.spec_file, 'r') as f:
        spec_content = f.read()
    
    parser = SpecParser()
    spec = parser.parse(spec_content)
    
    service_name = spec.name.lower().replace(' ', '-')
    if not is_safe_service_name(service_name):
        logger.error(f"Invalid service name: {service_name}")
        sys.exit(1)
    
    # Generate code
    generator = CodeGenerator(debug=args.debug)
    files = generator.generate_cloud_function(spec, args.runtime)
    
    # Create temporary directory for deployment
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write files
        for filename, content in files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        # Deploy using cloud provider
        logger.info(f"Deploying to {args.provider}...")
        
        provider = ProviderFactory.create(
            args.provider,
            project_id=args.project,
            region=args.region or 'us-central1',
            logger=logger
        )
        
        # Validate provider configuration
        config_errors = provider.validate_config()
        if config_errors:
            logger.error("Provider configuration validation failed:")
            for error in config_errors:
                logger.error(f"  • {error}")
            sys.exit(1)
        
        success = provider.deploy(service_name, temp_dir)
        
        if success:
            service_url = provider.get_service_url(service_name)
            logger.info(f"✅ Deployment successful!")
            logger.info(f"🌐 Service URL: {service_url}")
        else:
            logger.error("❌ Deployment failed")
            sys.exit(1)


def handle_list(args, logger):
    """Handle the list command"""
    provider = ProviderFactory.create(
        args.provider,
        project_id=args.project,
        region=args.region or 'us-central1',
        logger=logger
    )
    
    services = provider.list_services()
    
    if not services:
        logger.info("No services found")
        return
    
    logger.info(f"Found {len(services)} services:")
    for service in services:
        logger.info(f"  • {service['name']} - {service['url']} ({service['status']})")


def handle_logs(args, logger):
    """Handle the logs command"""
    provider = ProviderFactory.create(
        args.provider,
        project_id=args.project,
        region=args.region or 'us-central1',
        logger=logger
    )
    
    logs = provider.get_logs(args.service_name, args.limit)
    
    if not logs:
        logger.info("No logs found")
        return
    
    logger.info(f"Recent logs for {args.service_name}:")
    for log_entry in logs:
        print(log_entry)


def handle_delete(args, logger):
    """Handle the delete command"""
    if not args.yes:
        response = input(f"Are you sure you want to delete service '{args.service_name}'? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            logger.info("Operation cancelled")
            return
    
    provider = ProviderFactory.create(
        args.provider,
        project_id=args.project,
        region=args.region or 'us-central1',
        logger=logger
    )
    
    success = provider.delete_service(args.service_name)
    
    if success:
        logger.info(f"✅ Service '{args.service_name}' deleted successfully")
    else:
        logger.error(f"❌ Failed to delete service '{args.service_name}'")
        sys.exit(1)


if __name__ == '__main__':
    main()