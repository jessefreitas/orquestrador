"""
Sistema de logs internos avançado do Orquestrador
"""

import logging
import json
import os
import gzip
import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import threading
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Níveis de log customizados"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    AUDIT = 60


@dataclass
class LogEntry:
    """Entrada de log estruturada"""
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    exception: Optional[Dict[str, Any]] = None


class StructuredFormatter(logging.Formatter):
    """Formatador estruturado para logs JSON"""
    
    def __init__(self, session_id: str = None):
        super().__init__()
        self.session_id = session_id or f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def format(self, record: logging.LogRecord) -> str:
        # Criar entrada estruturada
        log_entry = LogEntry(
            timestamp=datetime.datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            thread_id=record.thread,
            process_id=record.process,
            session_id=self.session_id,
            metadata=getattr(record, 'metadata', None)
        )
        
        # Adicionar informações de exceção se houver
        if record.exc_info:
            log_entry.exception = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(asdict(log_entry), ensure_ascii=False)


class LogAnalyzer:
    """Analisador de logs"""
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
    
    def get_log_stats(self, log_file: str = None) -> Dict[str, Any]:
        """Obtém estatísticas dos logs"""
        if log_file:
            log_files = [self.log_dir / log_file]
        else:
            log_files = list(self.log_dir.glob("*.jsonl"))
        
        stats = {
            "total_entries": 0,
            "levels": {},
            "loggers": {},
            "time_range": {"start": None, "end": None},
            "errors": [],
            "warnings": [],
            "performance_metrics": {}
        }
        
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            stats["total_entries"] += 1
                            
                            # Contadores por nível
                            level = entry.get("level", "UNKNOWN")
                            stats["levels"][level] = stats["levels"].get(level, 0) + 1
                            
                            # Contadores por logger
                            logger = entry.get("logger", "UNKNOWN")
                            stats["loggers"][logger] = stats["loggers"].get(logger, 0) + 1
                            
                            # Range de tempo
                            timestamp = entry.get("timestamp")
                            if timestamp:
                                if not stats["time_range"]["start"] or timestamp < stats["time_range"]["start"]:
                                    stats["time_range"]["start"] = timestamp
                                if not stats["time_range"]["end"] or timestamp > stats["time_range"]["end"]:
                                    stats["time_range"]["end"] = timestamp
                            
                            # Coletar erros e warnings
                            if level == "ERROR":
                                stats["errors"].append({
                                    "timestamp": timestamp,
                                    "message": entry.get("message"),
                                    "module": entry.get("module")
                                })
                            elif level == "WARNING":
                                stats["warnings"].append({
                                    "timestamp": timestamp,
                                    "message": entry.get("message"),
                                    "module": entry.get("module")
                                })
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                print(f"Erro ao analisar {log_file}: {e}")
        
        return stats
    
    def search_logs(
        self,
        query: str = None,
        level: str = None,
        start_time: str = None,
        end_time: str = None,
        logger: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Busca logs com filtros"""
        results = []
        log_files = list(self.log_dir.glob("*.jsonl"))
        
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(results) >= limit:
                            break
                            
                        try:
                            entry = json.loads(line.strip())
                            
                            # Aplicar filtros
                            if level and entry.get("level") != level:
                                continue
                            if logger and entry.get("logger") != logger:
                                continue
                            if start_time and entry.get("timestamp", "") < start_time:
                                continue
                            if end_time and entry.get("timestamp", "") > end_time:
                                continue
                            if query and query.lower() not in entry.get("message", "").lower():
                                continue
                            
                            results.append(entry)
                            
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                print(f"Erro ao buscar em {log_file}: {e}")
        
        return results


class InternalLogManager:
    """Gerenciador de logs internos do Orquestrador"""
    
    def __init__(
        self,
        log_dir: str = "logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        compress_backups: bool = True
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.compress_backups = compress_backups
        
        # ID da sessão atual
        self.session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Configurar loggers
        self._setup_loggers()
        
        # Analisador de logs
        self.analyzer = LogAnalyzer(str(self.log_dir))
        
        # Thread para rotação automática
        self._rotation_thread = None
        self._should_rotate = threading.Event()
    
    def _setup_loggers(self):
        """Configura os loggers internos"""
        # Logger principal estruturado
        self.structured_logger = logging.getLogger("orquestrador.structured")
        self.structured_logger.setLevel(logging.DEBUG)
        
        # Handler para logs estruturados (JSON Lines)
        structured_handler = RotatingFileHandler(
            self.log_dir / "orquestrador_structured.jsonl",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        structured_handler.setFormatter(StructuredFormatter(self.session_id))
        self.structured_logger.addHandler(structured_handler)
        
        # Logger de auditoria
        self.audit_logger = logging.getLogger("orquestrador.audit")
        self.audit_logger.setLevel(logging.INFO)
        
        audit_handler = TimedRotatingFileHandler(
            self.log_dir / "audit.log",
            when="midnight",
            interval=1,
            backupCount=30
        )
        audit_handler.setFormatter(StructuredFormatter(self.session_id))
        self.audit_logger.addHandler(audit_handler)
        
        # Logger de performance
        self.performance_logger = logging.getLogger("orquestrador.performance")
        self.performance_logger.setLevel(logging.INFO)
        
        perf_handler = TimedRotatingFileHandler(
            self.log_dir / "performance.jsonl",
            when="midnight",
            interval=1,
            backupCount=7
        )
        perf_handler.setFormatter(StructuredFormatter(self.session_id))
        self.performance_logger.addHandler(perf_handler)
        
        # Logger de sistema
        self.system_logger = logging.getLogger("orquestrador.system")
        self.system_logger.setLevel(logging.DEBUG)
        
        system_handler = RotatingFileHandler(
            self.log_dir / "system.jsonl",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        system_handler.setFormatter(StructuredFormatter(self.session_id))
        self.system_logger.addHandler(system_handler)
    
    def log_execution_start(self, execution_id: str, metadata: Dict[str, Any] = None):
        """Log de início de execução"""
        self.structured_logger.info(
            f"Iniciando execução: {execution_id}",
            extra={
                "metadata": {
                    "event_type": "execution_start",
                    "execution_id": execution_id,
                    "session_id": self.session_id,
                    **(metadata or {})
                }
            }
        )
    
    def log_execution_end(self, execution_id: str, success: bool, duration: float, metadata: Dict[str, Any] = None):
        """Log de fim de execução"""
        self.structured_logger.info(
            f"Execução finalizada: {execution_id} - {'Sucesso' if success else 'Falha'}",
            extra={
                "metadata": {
                    "event_type": "execution_end",
                    "execution_id": execution_id,
                    "success": success,
                    "duration": duration,
                    "session_id": self.session_id,
                    **(metadata or {})
                }
            }
        )
    
    def log_task_event(self, task_name: str, event: str, metadata: Dict[str, Any] = None):
        """Log de eventos de tarefa"""
        self.structured_logger.info(
            f"Tarefa {task_name}: {event}",
            extra={
                "metadata": {
                    "event_type": "task_event",
                    "task_name": task_name,
                    "event": event,
                    "session_id": self.session_id,
                    **(metadata or {})
                }
            }
        )
    
    def log_performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Log de performance"""
        self.performance_logger.info(
            f"Performance: {operation}",
            extra={
                "metadata": {
                    "event_type": "performance",
                    "operation": operation,
                    "duration": duration,
                    "session_id": self.session_id,
                    **(metadata or {})
                }
            }
        )
    
    def log_audit(self, action: str, user: str = None, metadata: Dict[str, Any] = None):
        """Log de auditoria"""
        self.audit_logger.info(
            f"Audit: {action}",
            extra={
                "metadata": {
                    "event_type": "audit",
                    "action": action,
                    "user": user,
                    "session_id": self.session_id,
                    **(metadata or {})
                }
            }
        )
    
    def log_system_event(self, event: str, level: str = "INFO", metadata: Dict[str, Any] = None):
        """Log de eventos do sistema"""
        log_func = getattr(self.system_logger, level.lower(), self.system_logger.info)
        log_func(
            f"System: {event}",
            extra={
                "metadata": {
                    "event_type": "system",
                    "event": event,
                    "session_id": self.session_id,
                    **(metadata or {})
                }
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos logs"""
        return self.analyzer.get_log_stats()
    
    def search(self, **kwargs) -> List[Dict[str, Any]]:
        """Busca logs"""
        return self.analyzer.search_logs(**kwargs)
    
    def rotate_logs(self):
        """Força rotação dos logs"""
        for handler in logging.getLogger().handlers:
            if hasattr(handler, 'doRollover'):
                handler.doRollover()
    
    def compress_old_logs(self):
        """Comprime logs antigos"""
        if not self.compress_backups:
            return
        
        for log_file in self.log_dir.glob("*.log.*"):
            if not log_file.name.endswith('.gz'):
                try:
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                            f_out.writelines(f_in)
                    log_file.unlink()  # Remove arquivo original
                except Exception as e:
                    print(f"Erro ao comprimir {log_file}: {e}")
    
    def cleanup_old_logs(self, days: int = 30):
        """Remove logs antigos"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        for log_file in self.log_dir.glob("*"):
            if log_file.is_file():
                file_date = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_date < cutoff_date:
                    try:
                        log_file.unlink()
                        print(f"Log removido: {log_file}")
                    except Exception as e:
                        print(f"Erro ao remover {log_file}: {e}")
    
    def export_logs(self, output_file: str, start_date: str = None, end_date: str = None):
        """Exporta logs para arquivo"""
        results = self.search(start_time=start_date, end_time=end_date, limit=10000)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return len(results)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Retorna informações da sessão atual"""
        return {
            "session_id": self.session_id,
            "start_time": datetime.datetime.now().isoformat(),
            "log_dir": str(self.log_dir),
            "active_loggers": [
                "structured",
                "audit", 
                "performance",
                "system"
            ]
        } 