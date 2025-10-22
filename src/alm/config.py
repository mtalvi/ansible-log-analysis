#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration management for Ansible Error RAG System.
Loads settings from .env file.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class EmbeddingsConfig:
    """Configuration for embedding model."""
    
    def __init__(self):
        self.model_name = os.getenv('EMBEDDINGS_LLM_MODEL_NAME', 'nomic-ai/nomic-embed-text-v1.5')
        self.api_url = os.getenv('EMBEDDINGS_LLM_URL', '').strip()
        self.api_key = os.getenv('EMBEDDINGS_LLM_API_KEY', '').strip()
        
    @property
    def is_local(self) -> bool:
        """Check if using local model (not API-based)."""
        return not self.api_url
    
    @property
    def is_api(self) -> bool:
        """Check if using API-based embeddings."""
        return bool(self.api_url)
    
    @property
    def requires_api_key(self) -> bool:
        """Check if API key is required and missing."""
        return self.is_api and not self.api_key
    
    def validate(self):
        """Validate configuration."""
        if not self.model_name:
            raise ValueError("EMBEDDINGS_LLM_MODEL_NAME must be set")
        
        if self.is_api and not self.api_key:
            raise ValueError(
                f"EMBEDDINGS_LLM_API_KEY is required when using API endpoint: {self.api_url}"
            )
    
    def __repr__(self):
        return (
            f"EmbeddingsConfig(\n"
            f"  model_name={self.model_name}\n"
            f"  mode={'API' if self.is_api else 'LOCAL'}\n"
            f"  api_url={self.api_url or 'N/A'}\n"
            f"  api_key={'***' + self.api_key[-4:] if self.api_key else 'N/A'}\n"
            f")"
        )


class StorageConfig:
    """Configuration for data storage paths."""
    
    def __init__(self):
        self.data_dir = Path(os.getenv('DATA_DIR', './data'))
        self.knowledge_base_dir = Path(os.getenv('KNOWLEDGE_BASE_DIR', './knowledge_base'))
        
    @property
    def index_path(self) -> str:
        """Path to FAISS index file."""
        return str(self.data_dir / 'ansible_errors.index')
    
    @property
    def metadata_path(self) -> str:
        """Path to metadata pickle file."""
        return str(self.data_dir / 'error_metadata.pkl')
    
    def ensure_directories(self):
        """Create directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
    
    def __repr__(self):
        return (
            f"StorageConfig(\n"
            f"  data_dir={self.data_dir}\n"
            f"  knowledge_base_dir={self.knowledge_base_dir}\n"
            f"  index_path={self.index_path}\n"
            f"  metadata_path={self.metadata_path}\n"
            f")"
        )


class Config:
    """Main configuration object."""
    
    def __init__(self):
        self.embeddings = EmbeddingsConfig()
        self.storage = StorageConfig()
        
    def validate(self):
        """Validate all configuration."""
        self.embeddings.validate()
        self.storage.ensure_directories()
    
    def print_config(self):
        """Print configuration summary."""
        print("=" * 70)
        print("CONFIGURATION")
        print("=" * 70)
        print(self.embeddings)
        print(self.storage)
        print("=" * 70)


# Global config instance
config = Config()


if __name__ == "__main__":
    # Test configuration loading
    config.print_config()
    config.validate()
    print("\n✓ Configuration validated successfully")