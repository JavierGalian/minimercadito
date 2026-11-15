"""Compatibilidad para importaciones existentes del módulo de base de datos."""

from .core.database import Base, get_db

__all__ = ["Base", "get_db"]
