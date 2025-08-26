# Legacy Implementation

This directory contains the original Cloud Run-only implementation that was superseded by the Terraform multi-cloud approach.

## Contents

- `prototype.py` - Original main entry point (GCP Cloud Run only)
- `code_generator.py` - Original code generation using Claude AI
- `cloud_run_deployer.py` - Direct Cloud Run deployment without Terraform
- `examples/` - Legacy specification examples

## Usage

The legacy implementation is still functional and can be accessed via:

```bash
# Direct legacy usage
python legacy/prototype.py legacy/examples/example-spec.md --verbose

# Or via the main prototype with legacy flag
python terraform_prototype.py legacy/examples/example-spec.md --legacy
```

## Migration Note

For new projects, use the main Terraform implementation (`terraform_prototype.py`) which supports:
- Multi-cloud deployments (GCP, AWS, Azure)
- Infrastructure as Code with Terraform
- Better state management
- Enhanced monitoring and logging