"""
Classe principal do Orquestrador
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .task import Task, TaskStatus
from .utils import setup_logger, validate_dependencies, topological_sort, format_duration


class Orquestrador:
    """
    Classe principal para orquestração de tarefas
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        log_level: str = "INFO",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa o orquestrador
        
        Args:
            max_workers: Número máximo de workers para execução paralela
            log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            config: Configurações adicionais
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, Task] = {}
        self.execution_order: List[str] = []
        self.logger = setup_logger(self.__class__.__name__, log_level)
        self.config = config or {}
        
        # Estado da execução
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
    
    def add_task(
        self,
        name: str,
        function: Callable,
        dependencies: Optional[List[str]] = None,
        description: Optional[str] = None,
        timeout: Optional[int] = None,
        retry_count: int = 0,
        **kwargs
    ) -> Task:
        """
        Adiciona uma nova tarefa ao orquestrador
        
        Args:
            name: Nome único da tarefa
            function: Função a ser executada
            dependencies: Lista de nomes de tarefas que devem ser executadas antes
            description: Descrição da tarefa
            timeout: Timeout em segundos para execução
            retry_count: Número de tentativas em caso de falha
            **kwargs: Argumentos adicionais para a função
        
        Returns:
            Instância da tarefa criada
        """
        if name in self.tasks:
            raise ValueError(f"Tarefa '{name}' já existe")
        
        task = Task(
            name=name,
            function=function,
            dependencies=dependencies,
            description=description,
            timeout=timeout,
            retry_count=retry_count,
            **kwargs
        )
        
        self.tasks[name] = task
        self.logger.info(f"Tarefa '{name}' adicionada")
        
        return task
    
    def remove_task(self, name: str):
        """
        Remove uma tarefa do orquestrador
        
        Args:
            name: Nome da tarefa a ser removida
        """
        if name not in self.tasks:
            raise ValueError(f"Tarefa '{name}' não encontrada")
        
        # Verificar se outras tarefas dependem desta
        dependents = []
        for task_name, task in self.tasks.items():
            if name in task.dependencies:
                dependents.append(task_name)
        
        if dependents:
            raise ValueError(
                f"Não é possível remover a tarefa '{name}'. "
                f"As seguintes tarefas dependem dela: {', '.join(dependents)}"
            )
        
        del self.tasks[name]
        self.logger.info(f"Tarefa '{name}' removida")
    
    def get_task(self, name: str) -> Task:
        """
        Retorna uma tarefa pelo nome
        
        Args:
            name: Nome da tarefa
        
        Returns:
            Instância da tarefa
        """
        if name not in self.tasks:
            raise ValueError(f"Tarefa '{name}' não encontrada")
        
        return self.tasks[name]
    
    def list_tasks(self) -> List[str]:
        """
        Retorna lista com nomes de todas as tarefas
        
        Returns:
            Lista de nomes de tarefas
        """
        return list(self.tasks.keys())
    
    def validate(self) -> List[str]:
        """
        Valida as tarefas e suas dependências
        
        Returns:
            Lista de erros encontrados
        """
        return validate_dependencies(self.tasks)
    
    def plan_execution(self) -> List[str]:
        """
        Planeja a ordem de execução das tarefas
        
        Returns:
            Lista ordenada de nomes de tarefas
        """
        errors = self.validate()
        if errors:
            raise ValueError(f"Erros de validação: {'; '.join(errors)}")
        
        self.execution_order = topological_sort(self.tasks)
        self.logger.info(f"Ordem de execução planejada: {' -> '.join(self.execution_order)}")
        
        return self.execution_order
    
    def run(self, parallel: bool = True) -> Dict[str, Any]:
        """
        Executa todas as tarefas
        
        Args:
            parallel: Se True, executa tarefas independentes em paralelo
        
        Returns:
            Dicionário com os resultados das tarefas
        """
        if self.is_running:
            raise RuntimeError("Orquestrador já está em execução")
        
        self.logger.info("Iniciando execução do orquestrador")
        self.is_running = True
        self.start_time = datetime.now()
        self.results = {}
        
        try:
            # Planejar execução
            self.plan_execution()
            
            if parallel:
                self._run_parallel()
            else:
                self._run_sequential()
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            self.logger.info(f"Execução concluída em {format_duration(duration)}")
            
            return self.results
        
        except Exception as e:
            self.logger.error(f"Erro durante execução: {e}")
            raise
        
        finally:
            self.is_running = False
    
    def _run_sequential(self):
        """Executa tarefas sequencialmente"""
        self.logger.info("Executando tarefas sequencialmente")
        
        for task_name in self.execution_order:
            task = self.tasks[task_name]
            self._execute_task(task)
    
    def _run_parallel(self):
        """Executa tarefas em paralelo quando possível"""
        self.logger.info(f"Executando tarefas em paralelo (max_workers={self.max_workers})")
        
        completed_tasks = set()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while len(completed_tasks) < len(self.tasks):
                # Encontrar tarefas prontas para execução
                ready_tasks = []
                for task_name in self.execution_order:
                    if task_name in completed_tasks:
                        continue
                    
                    task = self.tasks[task_name]
                    if all(dep in completed_tasks for dep in task.dependencies):
                        ready_tasks.append(task_name)
                
                if not ready_tasks:
                    break
                
                # Submeter tarefas prontas
                future_to_task = {}
                for task_name in ready_tasks:
                    task = self.tasks[task_name]
                    future = executor.submit(self._execute_task, task)
                    future_to_task[future] = task_name
                
                # Aguardar conclusão
                for future in as_completed(future_to_task):
                    task_name = future_to_task[future]
                    completed_tasks.add(task_name)
                    
                    try:
                        future.result()  # Capturar exceções
                    except Exception as e:
                        self.logger.error(f"Erro na tarefa '{task_name}': {e}")
                        raise
    
    def _execute_task(self, task: Task):
        """
        Executa uma tarefa individual
        
        Args:
            task: Tarefa a ser executada
        """
        self.logger.info(f"Iniciando execução da tarefa '{task.name}'")
        
        attempts = 0
        max_attempts = task.retry_count + 1
        
        while attempts < max_attempts:
            try:
                if attempts > 0:
                    self.logger.warning(f"Tentativa {attempts + 1} para tarefa '{task.name}'")
                
                result = task.execute()
                self.results[task.name] = result
                
                duration = task.duration or 0
                self.logger.info(
                    f"Tarefa '{task.name}' concluída com sucesso em {format_duration(duration)}"
                )
                return result
                
            except Exception as e:
                attempts += 1
                self.logger.error(f"Erro na tarefa '{task.name}' (tentativa {attempts}): {e}")
                
                if attempts >= max_attempts:
                    self.logger.error(f"Tarefa '{task.name}' falhou após {max_attempts} tentativas")
                    raise
                
                # Reset para nova tentativa
                task.reset()
                time.sleep(1)  # Pequeno delay entre tentativas
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do orquestrador
        
        Returns:
            Dicionário com informações de status
        """
        task_status = {}
        for name, task in self.tasks.items():
            task_status[name] = {
                'status': task.status.value,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'duration': task.duration,
                'attempts': task.attempts,
                'error': str(task.error) if task.error else None
            }
        
        return {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_tasks': len(self.tasks),
            'completed_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            'failed_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            'tasks': task_status
        }
    
    def reset(self):
        """Reset completo do orquestrador"""
        if self.is_running:
            raise RuntimeError("Não é possível resetar durante execução")
        
        for task in self.tasks.values():
            task.reset()
        
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.execution_order = []
        
        self.logger.info("Orquestrador resetado")
    
    def __str__(self) -> str:
        return f"Orquestrador(tasks={len(self.tasks)}, running={self.is_running})"
    
    def __repr__(self) -> str:
        return (f"Orquestrador(max_workers={self.max_workers}, "
                f"tasks={list(self.tasks.keys())}, running={self.is_running})") 