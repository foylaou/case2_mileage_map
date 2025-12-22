"""
路由模組
"""
from .upload import bp as upload_bp
from .calculate import bp as calculate_bp
from .export import bp as export_bp

__all__ = ['upload_bp', 'calculate_bp', 'export_bp']








