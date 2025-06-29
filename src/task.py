"""
Módulo para definição de tarefas
"""

from enum import Enum
from typing import Callable, List, Optional, Any
from datetime import datetime
import uuid


class TaskStatus(Enum):
    """Status possíveis de uma tarefa"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task:
    """
    Classe que representa uma tarefa no orquestrador
    """
    
    def __init__(
        self,
        name: str,
        function: Callable,
        dependencies: Optional[List[str]] = None,
        description: Optional[str] = None,
        timeout: Optional[int] = None,
        retry_count: int = 0,
        **kwargs
    ):
        """
        Inicializa uma nova tarefa
        
        Args:
            name: Nome único da tarefa
            function: Função a ser executada
            dependencies: Lista de nomes de tarefas que devem ser executadas antes
            description: Descrição da tarefa
            timeout: Timeout em segundos para execução
            retry_count: Número de tentativas em caso de falha
            **kwargs: Argumentos adicionais para a função
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.function = function
        self.dependencies = dependencies or []
        self.description = description or f"Tarefa: {name}"
        self.timeout = timeout
        self.retry_count = retry_count
        self.kwargs = kwargs
        
        # Estado da tarefa
        self.status = TaskStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.attempts = 0
    
    def execute(self) -> Any:
        """
        Executa a tarefa
        
        Returns:
            Resultado da execução da função
            
        Raises:
            Exception: Qualquer exceção lançada durante a execução
        """
        self.status = TaskStatus.RUNNING
        self.start_time = datetime.now()
        self.attempts += 1
        
        try:
            self.result = self.function(**self.kwargs)
            self.status = TaskStatus.COMPLETED
            self.end_time = datetime.now()
            return self.result
        except Exception as e:
            self.error = e
            self.status = TaskStatus.FAILED
            self.end_time = datetime.now()
            raise e
    
    def reset(self):
        """Reset do estado da tarefa"""
        self.status = TaskStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None
        self.attempts = 0
    
    @property
    def duration(self) -> Optional[float]:
        """
        Retorna a duração da execução em segundos
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def __str__(self) -> str:
        return f"Task(name='{self.name}', status={self.status.value})"
    
    def __repr__(self) -> str:
        return (f"Task(id='{self.id}', name='{self.name}', "
                f"status={self.status.value}, dependencies={self.dependencies})") 