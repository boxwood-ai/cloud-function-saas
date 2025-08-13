"""
Base cloud provider interface for deployment abstraction.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging


class CloudProvider(ABC):
    """Abstract base class for cloud providers"""
    
    def __init__(self, project_id: str, region: str, logger: Optional[logging.Logger] = None):
        self.project_id = project_id
        self.region = region
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    def deploy(self, service_name: str, source_dir: str) -> bool:
        """Deploy service to cloud provider"""
        pass
    
    @abstractmethod
    def get_service_url(self, service_name: str) -> str:
        """Get the public URL of a deployed service"""
        pass
    
    @abstractmethod
    def get_logs(self, service_name: str, limit: int = 100) -> List[str]:
        """Get recent logs for a service"""
        pass
    
    @abstractmethod
    def delete_service(self, service_name: str) -> bool:
        """Delete a deployed service"""
        pass
    
    @abstractmethod
    def list_services(self) -> List[Dict[str, str]]:
        """List all deployed services"""
        pass
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate provider configuration and return any errors"""
        pass


class DeploymentError(Exception):
    """Exception raised during deployment operations"""
    pass


class ProviderFactory:
    """Factory for creating cloud provider instances"""
    
    _providers = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a new provider"""
        cls._providers[name] = provider_class
    
    @classmethod
    def create(cls, provider_name: str, **kwargs) -> CloudProvider:
        """Create a provider instance"""
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return cls._providers[provider_name](**kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers"""
        return list(cls._providers.keys())