"""
Orquestrador - Sistema de orquestração de tarefas e processos automatizados
"""

from .orquestrador import Orquestrador
from .task import Task, TaskStatus
from .version import ReleaseManager, VersionInfo, get_version_info
from .backup import BackupManager
from .logging_system import InternalLogManager

__version__ = "1.1.0"
__author__ = "Jesse Freitas"
__email__ = "jesse@example.com"

__all__ = [
    "Orquestrador", 
    "Task", 
    "TaskStatus",
    "ReleaseManager",
    "VersionInfo", 
    "get_version_info",
    "BackupManager",
    "InternalLogManager"
] 