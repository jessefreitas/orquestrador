"""
Utilitários para o orquestrador
"""

import logging
import colorlog
from typing import Dict, List, Any
from datetime import datetime
import yaml
import json
import os


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Configura e retorna um logger com formatação colorida
    
    Args:
        name: Nome do logger
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evita duplicação de handlers
    if logger.handlers:
        return logger
    
    # Handler para console com cores
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(
        colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    )
    logger.addHandler(console_handler)
    
    # Handler para arquivo
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler(
        f'logs/orquestrador_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    logger.addHandler(file_handler)
    
    return logger


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Carrega configuração de arquivo YAML ou JSON
    
    Args:
        config_path: Caminho para o arquivo de configuração
    
    Returns:
        Dicionário com as configurações
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as file:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            return yaml.safe_load(file)
        elif config_path.endswith('.json'):
            return json.load(file)
        else:
            raise ValueError("Formato de arquivo não suportado. Use YAML ou JSON.")


def save_config(config: Dict[str, Any], config_path: str):
    """
    Salva configuração em arquivo YAML ou JSON
    
    Args:
        config: Dicionário com as configurações
        config_path: Caminho para salvar o arquivo
    """
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as file:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
        elif config_path.endswith('.json'):
            json.dump(config, file, indent=2, ensure_ascii=False)
        else:
            raise ValueError("Formato de arquivo não suportado. Use YAML ou JSON.")


def validate_dependencies(tasks: Dict[str, Any]) -> List[str]:
    """
    Valida se as dependências das tarefas são válidas
    
    Args:
        tasks: Dicionário com as tarefas
    
    Returns:
        Lista de erros encontrados
    """
    errors = []
    task_names = set(tasks.keys())
    
    for task_name, task in tasks.items():
        dependencies = task.dependencies if hasattr(task, 'dependencies') else []
        
        for dep in dependencies:
            if dep not in task_names:
                errors.append(f"Tarefa '{task_name}' depende de '{dep}' que não existe")
    
    return errors


def topological_sort(tasks: Dict[str, Any]) -> List[str]:
    """
    Ordena as tarefas topologicamente baseado nas dependências
    
    Args:
        tasks: Dicionário com as tarefas
    
    Returns:
        Lista ordenada de nomes de tarefas
    """
    # Algoritmo de Kahn para ordenação topológica
    in_degree = {task: 0 for task in tasks}
    graph = {task: [] for task in tasks}
    
    # Construir grafo e calcular grau de entrada
    for task_name, task in tasks.items():
        dependencies = task.dependencies if hasattr(task, 'dependencies') else []
        for dep in dependencies:
            graph[dep].append(task_name)
            in_degree[task_name] += 1
    
    # Encontrar nós sem dependências
    queue = [task for task, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        current = queue.pop(0)
        result.append(current)
        
        # Reduzir grau de entrada dos vizinhos
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Verificar se há ciclos
    if len(result) != len(tasks):
        raise ValueError("Dependências circulares detectadas")
    
    return result


def format_duration(seconds: float) -> str:
    """
    Formata duração em segundos para formato legível
    
    Args:
        seconds: Duração em segundos
    
    Returns:
        String formatada (ex: "1h 30m 45s")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes = int(seconds // 60)
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {seconds:.2f}s"
    
    hours = int(minutes // 60)
    minutes = minutes % 60
    
    return f"{hours}h {minutes}m {seconds:.2f}s" 