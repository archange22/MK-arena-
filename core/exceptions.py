"""NOVA Exception definitions"""

class NovaException(Exception):
    """Base exception for NOVA"""
    pass

class SecurityException(NovaException):
    """Raised when an action violates security policy"""
    pass

class ToolExecutionException(NovaException):
    """Raised when a tool execution fails"""
    pass

class TaskExecutionException(NovaException):
    """Raised when an agent task fails"""
    pass

class MemoryException(NovaException):
    """Raised on memory storage or retrieval failure"""
    pass
