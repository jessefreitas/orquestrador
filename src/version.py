"""
Sistema de versionamento e releases do Orquestrador
"""

import os
import json
import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

__version__ = "1.0.0"
__release_date__ = "2025-06-29"
__build__ = "20250629001"


@dataclass
class VersionInfo:
    """Informações de versão"""
    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    build: Optional[str] = None
    release_date: Optional[str] = None
    
    @property
    def version_string(self) -> str:
        """Retorna string da versão"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    @classmethod
    def from_string(cls, version_str: str) -> 'VersionInfo':
        """Cria VersionInfo a partir de string"""
        # Parse semântico: major.minor.patch[-pre_release][+build]
        parts = version_str.split('+')
        version_part = parts[0]
        build = parts[1] if len(parts) > 1 else None
        
        version_parts = version_part.split('-')
        main_version = version_parts[0]
        pre_release = version_parts[1] if len(version_parts) > 1 else None
        
        major, minor, patch = map(int, main_version.split('.'))
        
        return cls(
            major=major,
            minor=minor,
            patch=patch,
            pre_release=pre_release,
            build=build
        )


class ReleaseManager:
    """Gerenciador de releases"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.releases_dir = self.project_root / "releases"
        self.releases_dir.mkdir(exist_ok=True)
        
        self.releases_file = self.releases_dir / "releases.json"
        self.current_version = VersionInfo.from_string(__version__)
        
        # Carregar histórico de releases
        self.releases_history = self._load_releases_history()
    
    def _load_releases_history(self) -> Dict[str, Any]:
        """Carrega histórico de releases"""
        if self.releases_file.exists():
            with open(self.releases_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"releases": [], "current": None}
    
    def _save_releases_history(self):
        """Salva histórico de releases"""
        with open(self.releases_file, 'w', encoding='utf-8') as f:
            json.dump(self.releases_history, f, indent=2, ensure_ascii=False)
    
    def create_release(
        self,
        version: Optional[str] = None,
        release_notes: str = "",
        pre_release: bool = False
    ) -> Dict[str, Any]:
        """
        Cria um novo release
        
        Args:
            version: Versão do release (se None, incrementa automaticamente)
            release_notes: Notas do release
            pre_release: Se é um pre-release
        
        Returns:
            Informações do release criado
        """
        # Determinar versão
        if version:
            new_version = VersionInfo.from_string(version)
        else:
            # Auto-incrementar patch
            new_version = VersionInfo(
                major=self.current_version.major,
                minor=self.current_version.minor,
                patch=self.current_version.patch + 1,
                build=datetime.datetime.now().strftime("%Y%m%d%H%M"),
                release_date=datetime.date.today().isoformat()
            )
        
        # Criar release
        release_info = {
            "version": new_version.version_string,
            "release_date": datetime.datetime.now().isoformat(),
            "pre_release": pre_release,
            "release_notes": release_notes,
            "build_info": {
                "build_date": datetime.datetime.now().isoformat(),
                "build_number": new_version.build,
                "python_version": os.sys.version,
                "platform": os.name
            },
            "files": self._get_project_files()
        }
        
        # Salvar release
        release_dir = self.releases_dir / f"v{new_version.version_string}"
        release_dir.mkdir(exist_ok=True)
        
        release_file = release_dir / "release.json"
        with open(release_file, 'w', encoding='utf-8') as f:
            json.dump(release_info, f, indent=2, ensure_ascii=False)
        
        # Atualizar histórico
        self.releases_history["releases"].append(release_info)
        self.releases_history["current"] = release_info
        self._save_releases_history()
        
        # Atualizar versão atual
        self.current_version = new_version
        
        return release_info
    
    def _get_project_files(self) -> Dict[str, Any]:
        """Lista arquivos do projeto"""
        files_info = {}
        
        # Principais diretórios e arquivos
        important_paths = [
            "src/",
            "config/",
            "examples/",
            "tests/",
            "main.py",
            "requirements.txt",
            "README.md"
        ]
        
        for path_str in important_paths:
            path = self.project_root / path_str
            if path.exists():
                if path.is_file():
                    files_info[path_str] = {
                        "type": "file",
                        "size": path.stat().st_size,
                        "modified": datetime.datetime.fromtimestamp(
                            path.stat().st_mtime
                        ).isoformat()
                    }
                elif path.is_dir():
                    files_info[path_str] = {
                        "type": "directory",
                        "files": len(list(path.rglob("*"))),
                        "modified": datetime.datetime.fromtimestamp(
                            path.stat().st_mtime
                        ).isoformat()
                    }
        
        return files_info
    
    def list_releases(self) -> list:
        """Lista todos os releases"""
        return self.releases_history.get("releases", [])
    
    def get_release(self, version: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de um release específico"""
        for release in self.releases_history.get("releases", []):
            if release["version"] == version:
                return release
        return None
    
    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """Obtém o último release"""
        releases = self.releases_history.get("releases", [])
        return releases[-1] if releases else None
    
    def create_changelog(self) -> str:
        """Gera changelog baseado nos releases"""
        changelog = ["# Changelog", ""]
        
        for release in reversed(self.releases_history.get("releases", [])):
            version = release["version"]
            date = release["release_date"][:10]  # YYYY-MM-DD
            pre_release = " (Pre-release)" if release.get("pre_release") else ""
            
            changelog.append(f"## [{version}]{pre_release} - {date}")
            changelog.append("")
            
            if release.get("release_notes"):
                changelog.append(release["release_notes"])
            else:
                changelog.append("- Melhorias e correções")
            
            changelog.append("")
        
        return "\n".join(changelog)


def get_version_info() -> Dict[str, Any]:
    """Retorna informações completas de versão"""
    return {
        "version": __version__,
        "release_date": __release_date__,
        "build": __build__,
        "full_version": f"{__version__}+{__build__}",
        "build_date": datetime.datetime.now().isoformat(),
        "python_version": os.sys.version,
        "platform": os.name
    }


def check_for_updates() -> Dict[str, Any]:
    """Verifica se há atualizações disponíveis"""
    # Implementação futura para verificar updates remotos
    return {
        "current_version": __version__,
        "latest_version": __version__,
        "update_available": False,
        "update_url": None
    } 