"""
Orquestrador - Sistema de orquestração de tarefas e processos automatizados
"""

from .orquestrador import Orquestrador
from .task import Task, TaskStatus

__version__ = "1.0.0"
__author__ = "Jesse Freitas"
__email__ = "jesse@example.com"

__all__ = ["Orquestrador", "Task", "TaskStatus"] 