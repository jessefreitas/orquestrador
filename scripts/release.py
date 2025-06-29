#!/usr/bin/env python3
"""
Script de automação de releases
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))

from src.version import ReleaseManager, get_version_info
from src.backup import BackupManager
from src.logging_system import InternalLogManager


def run_command(command, check=True):
    """Executa comando e retorna resultado"""
    print(f"🔄 Executando: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"❌ Erro: {result.stderr}")
        sys.exit(1)
    
    return result


def create_git_tag(version):
    """Cria tag Git para o release"""
    tag_name = f"v{version}"
    
    # Verificar se tag já existe
    result = run_command(f"git tag -l {tag_name}", check=False)
    if tag_name in result.stdout:
        print(f"⚠️ Tag {tag_name} já existe")
        return False
    
    # Criar tag
    run_command(f"git tag -a {tag_name} -m 'Release {version}'")
    print(f"🏷️ Tag {tag_name} criada")
    
    return True


def run_tests():
    """Executa testes antes do release"""
    print("🧪 Executando testes...")
    
    # Verificar se pytest está disponível
    result = run_command("python -m pytest --version", check=False)
    if result.returncode != 0:
        print("⚠️ pytest não encontrado, pulando testes")
        return True
    
    # Executar testes
    result = run_command("python -m pytest tests/ -v", check=False)
    if result.returncode != 0:
        print("❌ Testes falharam!")
        return False
    
    print("✅ Todos os testes passaram!")
    return True


def update_version_files(version):
    """Atualiza arquivos de versão"""
    print(f"📝 Atualizando versão para {version}...")
    
    # Atualizar src/__init__.py
    init_file = Path("src/__init__.py")
    if init_file.exists():
        content = init_file.read_text(encoding='utf-8')
        content = content.replace(
            '__version__ = "1.1.0"',
            f'__version__ = "{version}"'
        )
        init_file.write_text(content, encoding='utf-8')
        print(f"✅ {init_file} atualizado")
    
    # Atualizar src/version.py
    version_file = Path("src/version.py")
    if version_file.exists():
        content = version_file.read_text(encoding='utf-8')
        content = content.replace(
            '__version__ = "1.0.0"',
            f'__version__ = "{version}"'
        )
        version_file.write_text(content, encoding='utf-8')
        print(f"✅ {version_file} atualizado")
    
    # Atualizar setup.py
    setup_file = Path("setup.py")
    if setup_file.exists():
        content = setup_file.read_text(encoding='utf-8')
        content = content.replace(
            'version="1.1.0"',
            f'version="{version}"'
        )
        setup_file.write_text(content, encoding='utf-8')
        print(f"✅ {setup_file} atualizado")


def build_package():
    """Constrói o pacote Python"""
    print("📦 Construindo pacote...")
    
    # Instalar build tools se necessário
    run_command("python -m pip install --upgrade build", check=False)
    
    # Limpar builds anteriores
    for path in ["build", "dist", "*.egg-info"]:
        run_command(f"rm -rf {path}", check=False)
    
    # Construir pacote
    run_command("python -m build")
    print("✅ Pacote construído!")


def create_release_workflow(version, release_notes, create_tag, push_changes, create_backup):
    """Workflow completo de release"""
    print(f"🚀 Iniciando release {version}")
    print("=" * 50)
    
    # 1. Criar backup antes de qualquer mudança
    if create_backup:
        print("💾 Criando backup de segurança...")
        backup_manager = BackupManager()
        backup = backup_manager.create_backup(
            name=f"pre_release_{version}",
            description=f"Backup antes do release {version}"
        )
        print(f"✅ Backup criado: {backup['name']}")
    
    # 2. Executar testes
    if not run_tests():
        print("❌ Release cancelado devido a falhas nos testes")
        return False
    
    # 3. Atualizar arquivos de versão
    update_version_files(version)
    
    # 4. Criar release no sistema interno
    print("🏷️ Criando release...")
    release_manager = ReleaseManager()
    log_manager = InternalLogManager()
    
    release_info = release_manager.create_release(
        version=version,
        release_notes=release_notes
    )
    
    # Log do release
    log_manager.log_audit(
        f"release_created",
        user="sistema",
        metadata={
            "version": version,
            "release_notes": release_notes[:100],
            "automated": True
        }
    )
    
    print(f"✅ Release {version} criado!")
    
    # 5. Gerar changelog
    print("📄 Gerando changelog...")
    changelog = release_manager.create_changelog()
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog)
    print("✅ CHANGELOG.md atualizado!")
    
    # 6. Commit das mudanças
    if push_changes:
        print("📝 Fazendo commit das mudanças...")
        run_command("git add .")
        run_command(f'git commit -m "Release {version}"')
        print("✅ Mudanças commitadas!")
        
        # 7. Criar tag Git
        if create_tag:
            create_git_tag(version)
            
        # 8. Push para repositório
        print("🔄 Enviando para repositório...")
        run_command("git push origin master")
        
        if create_tag:
            run_command(f"git push origin v{version}")
        
        print("✅ Mudanças enviadas!")
    
    # 9. Construir pacote
    build_package()
    
    # 10. Criar backup final
    if create_backup:
        print("💾 Criando backup final...")
        final_backup = backup_manager.create_backup(
            name=f"release_{version}",
            description=f"Backup após release {version}"
        )
        print(f"✅ Backup final: {final_backup['name']}")
    
    print("\n🎉 Release concluído com sucesso!")
    print(f"📦 Versão: {version}")
    print(f"📅 Data: {release_info['release_date']}")
    print(f"📄 Notas: {release_notes}")
    
    return True


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Script de automação de releases do Orquestrador",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/release.py 1.2.0 -n "Nova versão com melhorias"
  python scripts/release.py 1.2.1 --no-tag --no-push
  python scripts/release.py 1.3.0-beta --pre-release
        """
    )
    
    parser.add_argument("version", help="Versão do release (ex: 1.2.0)")
    parser.add_argument("-n", "--notes", default="", help="Notas do release")
    parser.add_argument("--pre-release", action="store_true", help="Marcar como pre-release")
    parser.add_argument("--no-tag", action="store_true", help="Não criar tag Git")
    parser.add_argument("--no-push", action="store_true", help="Não fazer push das mudanças")
    parser.add_argument("--no-backup", action="store_true", help="Não criar backups")
    parser.add_argument("--dry-run", action="store_true", help="Simular sem fazer mudanças")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 Modo simulação ativado - nenhuma mudança será feita")
        return
    
    # Verificar se estamos no diretório do projeto
    if not Path("src").exists() or not Path("README.md").exists():
        print("❌ Execute este script a partir do diretório raiz do projeto")
        sys.exit(1)
    
    # Verificar status do Git
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        print("⚠️ Há mudanças não commitadas no repositório")
        response = input("Continuar mesmo assim? (y/N): ")
        if response.lower() != 'y':
            print("❌ Release cancelado")
            sys.exit(1)
    
    # Executar workflow de release
    success = create_release_workflow(
        version=args.version,
        release_notes=args.notes,
        create_tag=not args.no_tag,
        push_changes=not args.no_push,
        create_backup=not args.no_backup
    )
    
    if not success:
        print("❌ Release falhou!")
        sys.exit(1)
    
    print("\n✨ Release completado com sucesso!")


if __name__ == "__main__":
    main() 