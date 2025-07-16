#!/usr/bin/env python3
"""
Configuration loader for document formatting system.
Loads settings from config.yaml and provides easy access to configuration values.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """Handles loading and accessing configuration settings."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory.
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            print(f"⚠️  Config file not found: {self.config_path}")
            print("📝 Creating default config.yaml...")
            self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config or {}
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}
    
    def _create_default_config(self):
        """Create a default configuration file."""
        default_config = {
            'input_path': '/path/to/your/original.docx',
            'output_path': '/path/to/your/formatted.docx',
            'known_path': '/path/to/your/target.docx',
            'default_method': 'multi-stage',
            'multi_stage': {
                'output_path': '/path/to/your/multi_stage_formatted.docx',
                'debug': True,
                'show_filtering_details': True
            },
            'pattern_based': {
                'output_path': '/path/to/your/pattern_based_formatted.docx',
                'strict_matching': True
            },
            'overnight_llm': {
                'output_path': '/path/to/your/overnight_llm_formatted.docx',
                'model_host': 'http://localhost:11434',
                'model_name': 'gemma3:27b-it-qat',
                'temperature': 0.1,
                'timeout': 20,
                'save_progress_every': 50
            },
            'analysis': {
                'enable_comparison': True,
                'show_debug_info': True,
                'export_metrics': True
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_input_path(self) -> str:
        """Get input document path."""
        return self.get('input_path', '')
    
    def get_output_path(self, method: str = None) -> str:
        """Get output path for specific method or default."""
        if method:
            method_output = self.get(f'{method}.output_path')
            if method_output:
                return method_output
        
        return self.get('output_path', '')
    
    def get_known_path(self) -> str:
        """Get known/target document path."""
        return self.get('known_path', '')
    
    def get_default_method(self) -> str:
        """Get default processing method."""
        return self.get('default_method', 'multi-stage')
    
    def get_method_config(self, method: str) -> Dict[str, Any]:
        """Get configuration for specific method."""
        return self.get(method, {})
    
    def validate_paths(self) -> Dict[str, bool]:
        """Validate that configured paths exist and are accessible."""
        paths = {
            'input_path': self.get_input_path(),
            'known_path': self.get_known_path()
        }
        
        results = {}
        for name, path in paths.items():
            if not path:
                results[name] = False
                continue
            
            path_obj = Path(path)
            results[name] = path_obj.exists() and path_obj.is_file()
        
        return results
    
    def print_config_summary(self):
        """Print a summary of current configuration."""
        print("📋 Configuration Summary:")
        print(f"   Input: {self.get_input_path()}")
        print(f"   Output: {self.get_output_path()}")
        print(f"   Known: {self.get_known_path()}")
        print(f"   Method: {self.get_default_method()}")
        
        validation = self.validate_paths()
        print("\n📁 Path Validation:")
        for name, exists in validation.items():
            status = "✅" if exists else "❌"
            print(f"   {name}: {status}")
        
        if not all(validation.values()):
            print("\n⚠️  Please update paths in config.yaml before running formatters.")

# Global configuration instance
config = ConfigLoader()

# Convenience functions
def get_input_path() -> str:
    """Get input document path."""
    return config.get_input_path()

def get_output_path(method: str = None) -> str:
    """Get output path for specific method."""
    return config.get_output_path(method)

def get_known_path() -> str:
    """Get known/target document path."""
    return config.get_known_path()

def get_default_method() -> str:
    """Get default processing method."""
    return config.get_default_method()

def get_method_config(method: str) -> Dict[str, Any]:
    """Get configuration for specific method."""
    return config.get_method_config(method)

def validate_config() -> bool:
    """Validate configuration and return True if valid."""
    validation = config.validate_paths()
    return all(validation.values())

def print_config_summary():
    """Print configuration summary."""
    config.print_config_summary()

if __name__ == "__main__":
    # Test configuration loading
    print("🔧 Testing Configuration Loader")
    print_config_summary()