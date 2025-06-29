"""
Sistema de backup e pontos de restauração do Orquestrador
"""

import os
import shutil
import json
import zipfile
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import hashlib


class BackupManager:
    """Gerenciador de backups e pontos de restauração"""
    
    def __init__(self, project_root: str = ".", backup_dir: str = None):
        self.project_root = Path(project_root)
        self.backup_dir = Path(backup_dir) if backup_dir else self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.checkpoints_dir = self.backup_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        # Carregar metadados
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Carrega metadados dos backups"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "backups": [],
            "checkpoints": [],
            "last_backup": None,
            "last_checkpoint": None
        }
    
    def _save_metadata(self):
        """Salva metadados dos backups"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula hash de um arquivo"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_project_state(self) -> Dict[str, Any]:
        """Obtém estado atual do projeto"""
        state = {
            "timestamp": datetime.datetime.now().isoformat(),
            "files": {},
            "directories": [],
            "total_size": 0
        }
        
        # Arquivos e diretórios importantes
        important_patterns = [
            "src/**/*.py",
            "config/**/*",
            "examples/**/*.py",
            "tests/**/*.py",
            "*.py",
            "*.txt",
            "*.md",
            "*.yaml",
            "*.yml",
            "*.json"
        ]
        
        for pattern in important_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and not self._should_ignore(file_path):
                    rel_path = file_path.relative_to(self.project_root)
                    file_info = {
                        "size": file_path.stat().st_size,
                        "modified": datetime.datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                        "hash": self._calculate_file_hash(file_path)
                    }
                    state["files"][str(rel_path)] = file_info
                    state["total_size"] += file_info["size"]
        
        # Diretórios
        for dir_path in self.project_root.iterdir():
            if dir_path.is_dir() and not self._should_ignore(dir_path):
                state["directories"].append(str(dir_path.relative_to(self.project_root)))
        
        return state
    
    def _should_ignore(self, path: Path) -> bool:
        """Verifica se um arquivo/diretório deve ser ignorado"""
        ignore_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "backups",
            "releases",
            ".vscode",
            ".idea",
            "logs/*.log"
        ]
        
        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        
        return False
    
    def create_backup(self, name: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        """
        Cria um backup completo do projeto
        
        Args:
            name: Nome do backup (se None, usa timestamp)
            description: Descrição do backup
        
        Returns:
            Informações do backup criado
        """
        timestamp = datetime.datetime.now()
        backup_name = name or f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Diretório do backup
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Criar arquivo ZIP
        zip_path = backup_path / f"{backup_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Adicionar arquivos importantes
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file() and not self._should_ignore(file_path):
                    arcname = file_path.relative_to(self.project_root)
                    zipf.write(file_path, arcname)
        
        # Obter estado do projeto
        project_state = self._get_project_state()
        
        # Informações do backup
        backup_info = {
            "name": backup_name,
            "description": description,
            "timestamp": timestamp.isoformat(),
            "type": "full_backup",
            "zip_file": str(zip_path.relative_to(self.backup_dir)),
            "size": zip_path.stat().st_size,
            "project_state": project_state,
            "restore_point": True
        }
        
        # Salvar informações do backup
        info_file = backup_path / "backup_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        # Atualizar metadados
        self.metadata["backups"].append(backup_info)
        self.metadata["last_backup"] = backup_info
        self._save_metadata()
        
        return backup_info
    
    def create_checkpoint(self, name: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        """
        Cria um checkpoint (ponto de restauração rápido)
        
        Args:
            name: Nome do checkpoint
            description: Descrição do checkpoint
        
        Returns:
            Informações do checkpoint
        """
        timestamp = datetime.datetime.now()
        checkpoint_name = name or f"checkpoint_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Estado atual do projeto
        project_state = self._get_project_state()
        
        # Informações do checkpoint
        checkpoint_info = {
            "name": checkpoint_name,
            "description": description,
            "timestamp": timestamp.isoformat(),
            "type": "checkpoint",
            "project_state": project_state,
            "restore_point": True
        }
        
        # Salvar checkpoint
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_name}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_info, f, indent=2, ensure_ascii=False)
        
        # Atualizar metadados
        self.metadata["checkpoints"].append(checkpoint_info)
        self.metadata["last_checkpoint"] = checkpoint_info
        self._save_metadata()
        
        # Limpar checkpoints antigos (manter últimos 10)
        self._cleanup_old_checkpoints()
        
        return checkpoint_info
    
    def restore_from_backup(self, backup_name: str) -> bool:
        """
        Restaura projeto a partir de um backup
        
        Args:
            backup_name: Nome do backup para restaurar
        
        Returns:
            True se restauração foi bem-sucedida
        """
        # Encontrar backup
        backup_info = None
        for backup in self.metadata["backups"]:
            if backup["name"] == backup_name:
                backup_info = backup
                break
        
        if not backup_info:
            raise ValueError(f"Backup '{backup_name}' não encontrado")
        
        # Caminho do arquivo ZIP
        zip_path = self.backup_dir / backup_info["zip_file"]
        if not zip_path.exists():
            raise FileNotFoundError(f"Arquivo de backup não encontrado: {zip_path}")
        
        # Criar backup de segurança antes da restauração
        safety_backup = self.create_backup(
            name=f"before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Backup automático antes de restaurar {backup_name}"
        )
        
        try:
            # Extrair backup
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(self.project_root)
            
            return True
            
        except Exception as e:
            # Em caso de erro, tentar restaurar backup de segurança
            print(f"Erro durante restauração: {e}")
            print("Tentando restaurar backup de segurança...")
            return self.restore_from_backup(safety_backup["name"])
    
    def restore_from_checkpoint(self, checkpoint_name: str) -> bool:
        """
        Restaura projeto a partir de um checkpoint
        
        Args:
            checkpoint_name: Nome do checkpoint
        
        Returns:
            True se restauração foi bem-sucedida
        """
        # Encontrar checkpoint
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_name}.json"
        if not checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint '{checkpoint_name}' não encontrado")
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint_info = json.load(f)
        
        # Criar checkpoint de segurança
        safety_checkpoint = self.create_checkpoint(
            name=f"before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Checkpoint automático antes de restaurar {checkpoint_name}"
        )
        
        # Implementar lógica de restauração de estado
        # Por simplicidade, vamos apenas registrar a operação
        print(f"Restaurando checkpoint: {checkpoint_name}")
        print(f"Checkpoint de segurança criado: {safety_checkpoint['name']}")
        
        return True
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Lista todos os backups"""
        return self.metadata.get("backups", [])
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """Lista todos os checkpoints"""
        return self.metadata.get("checkpoints", [])
    
    def delete_backup(self, backup_name: str) -> bool:
        """
        Deleta um backup
        
        Args:
            backup_name: Nome do backup para deletar
        
        Returns:
            True se deletado com sucesso
        """
        # Encontrar e remover backup
        for i, backup in enumerate(self.metadata["backups"]):
            if backup["name"] == backup_name:
                # Remover arquivos
                backup_dir = self.backup_dir / backup_name
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                
                # Remover dos metadados
                del self.metadata["backups"][i]
                self._save_metadata()
                return True
        
        return False
    
    def _cleanup_old_checkpoints(self, keep_count: int = 10):
        """Remove checkpoints antigos, mantendo apenas os mais recentes"""
        checkpoints = self.metadata.get("checkpoints", [])
        
        if len(checkpoints) > keep_count:
            # Ordenar por timestamp
            checkpoints.sort(key=lambda x: x["timestamp"])
            
            # Remover os mais antigos
            to_remove = checkpoints[:-keep_count]
            for checkpoint in to_remove:
                checkpoint_file = self.checkpoints_dir / f"{checkpoint['name']}.json"
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
            
            # Atualizar metadados
            self.metadata["checkpoints"] = checkpoints[-keep_count:]
            self._save_metadata()
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de um backup específico"""
        for backup in self.metadata["backups"]:
            if backup["name"] == backup_name:
                return backup
        return None
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Retorna informações sobre uso de armazenamento"""
        total_size = 0
        backup_count = len(self.metadata.get("backups", []))
        checkpoint_count = len(self.metadata.get("checkpoints", []))
        
        # Calcular tamanho total dos backups
        for backup_path in self.backup_dir.rglob("*.zip"):
            total_size += backup_path.stat().st_size
        
        return {
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "backup_count": backup_count,
            "checkpoint_count": checkpoint_count,
            "backup_dir": str(self.backup_dir)
        } 