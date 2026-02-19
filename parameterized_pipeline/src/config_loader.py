"""
Configuration Loader for Pipeline
This module loads YAML configuration files and makes them available to the pipeline.
"""

import yaml
from typing import Dict, Any


class ConfigLoader:
    """Loads and manages pipeline configuration from YAML files."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = {}
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            Dictionary containing the configuration
        """
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            print(f"✓ Successfully loaded configuration from: {config_path}")
            return self.config
        except FileNotFoundError:
            print(f"✗ Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            print(f"✗ Error parsing YAML file: {e}")
            raise
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the config value (e.g., 'general.kafka.main.host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            config.get('general.kafka.main.host')
            config.get('secrets.databricks_secret_scope')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_secrets(self) -> Dict[str, Any]:
        """Get the secrets section of the configuration."""
        return self.config.get('secrets', {})
    
    def get_general(self) -> Dict[str, Any]:
        """Get the general section of the configuration."""
        return self.config.get('general', {})
    
    def get_kafka_config(self) -> Dict[str, Any]:
        """Get the Kafka configuration."""
        return self.get_general().get('kafka', {})
    
    def get_streaming_config(self) -> Dict[str, Any]:
        """Get the streaming configuration."""
        return self.get_general().get('streaming', {})
    
    def get_secret_from_scope(self, secret_key: str) -> str:
        """
        Retrieve a secret from Databricks Secret Scope.
        
        Args:
            secret_key: The key of the secret to retrieve
            
        Returns:
            The secret value
        """
        try:
            from pyspark.sql import SparkSession
            from pyspark.dbutils import DBUtils
            
            spark = SparkSession.builder.getOrCreate()
            dbutils = DBUtils(spark)
            
            scope = self.get('secrets.databricks_secret_scope')
            if not scope:
                raise ValueError("databricks_secret_scope not found in configuration")
            
            return dbutils.secrets.get(scope=scope, key=secret_key)
        except Exception as e:
            print(f"✗ Error retrieving secret '{secret_key}': {e}")
            raise
    
    def display_config(self, mask_secrets: bool = True):
        """
        Display the loaded configuration.
        
        Args:
            mask_secrets: Whether to mask sensitive values
        """
        import json
        
        config_to_display = self.config.copy()
        
        if mask_secrets and 'secrets' in config_to_display:
            for key in config_to_display['secrets']:
                if config_to_display['secrets'][key]:
                    config_to_display['secrets'][key] = '***MASKED***'
        
        print("=" * 80)
        print("Configuration:")
        print("=" * 80)
        print(json.dumps(config_to_display, indent=2))
        print("=" * 80)


def load_config_from_spark_conf(spark, config_param: str = 'config_file_path') -> ConfigLoader:
    """
    Load configuration from a path specified in Spark configuration.
    
    Args:
        spark: SparkSession object
        config_param: Name of the spark config parameter containing the config file path
        
    Returns:
        ConfigLoader instance with loaded configuration
    """
    config_path = spark.conf.get(config_param)
    
    if not config_path:
        raise ValueError(f"Configuration parameter '{config_param}' not found in Spark config")
    
    return ConfigLoader(config_path)
