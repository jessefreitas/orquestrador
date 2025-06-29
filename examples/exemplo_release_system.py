#!/usr/bin/env python3
"""
Exemplo de uso do sistema de releases, backups e logs internos
"""

import sys
import os
import time

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.version import ReleaseManager, get_version_info
from src.backup import BackupManager
from src.logging_system import InternalLogManager


def exemplo_sistema_releases():
    """Demonstra o sistema de releases"""
    print("🏷️ Sistema de Releases")
    print("=" * 40)
    
    # Criar gerenciador de releases
    release_manager = ReleaseManager()
    
    # Mostrar versão atual
    version_info = get_version_info()
    print(f"📦 Versão atual: {version_info['version']}")
    print(f"🏗️ Build: {version_info['build']}")
    
    # Criar novo release
    print("\n🔄 Criando novo release...")
    release_info = release_manager.create_release(
        release_notes="""
        ✨ Novas funcionalidades:
        - Sistema de releases automático
        - Gerenciamento de backups
        - Logs internos estruturados
        - CLI para gerenciamento
        
        🔧 Melhorias:
        - Performance otimizada
        - Documentação atualizada
        - Testes expandidos
        """
    )
    
    print(f"✅ Release {release_info['version']} criado!")
    print(f"📅 Data: {release_info['release_date']}")
    
    # Listar releases
    print("\n📋 Histórico de releases:")
    releases = release_manager.list_releases()
    for release in releases[-3:]:  # Últimos 3
        version = release['version']
        date = release['release_date'][:10]
        print(f"   🏷️ {version} - {date}")
    
    # Gerar changelog
    print("\n📄 Gerando changelog...")
    changelog = release_manager.create_changelog()
    print("✅ Changelog gerado!")
    
    # Salvar changelog
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog)
    
    print("💾 Changelog salvo em CHANGELOG.md")
    return True


def exemplo_sistema_backups():
    """Demonstra o sistema de backups"""
    print("\n\n💾 Sistema de Backups")
    print("=" * 40)
    
    # Criar gerenciador de backups
    backup_manager = BackupManager()
    
    # Criar checkpoint inicial
    print("🔖 Criando checkpoint inicial...")
    checkpoint = backup_manager.create_checkpoint(
        name="exemplo_checkpoint",
        description="Checkpoint antes do exemplo de releases"
    )
    print(f"✅ Checkpoint '{checkpoint['name']}' criado!")
    
    # Criar backup completo
    print("\n📦 Criando backup completo...")
    backup_info = backup_manager.create_backup(
        name="backup_exemplo_v1_1",
        description="Backup após implementação do sistema de releases"
    )
    
    size_mb = backup_info['size'] / (1024 * 1024)
    print(f"✅ Backup '{backup_info['name']}' criado!")
    print(f"📊 Tamanho: {size_mb:.2f} MB")
    
    # Listar backups
    print("\n📋 Backups disponíveis:")
    backups = backup_manager.list_backups()
    for backup in backups[-3:]:  # Últimos 3
        name = backup['name']
        date = backup['timestamp'][:10]
        size_mb = backup['size'] / (1024 * 1024)
        print(f"   💾 {name} - {date} ({size_mb:.1f} MB)")
    
    # Informações de armazenamento
    storage = backup_manager.get_storage_usage()
    print(f"\n💽 Uso de armazenamento:")
    print(f"   📦 Backups: {storage['backup_count']}")
    print(f"   🔖 Checkpoints: {storage['checkpoint_count']}")
    print(f"   📊 Total: {storage['total_size_mb']:.2f} MB")
    
    return True


def exemplo_sistema_logs():
    """Demonstra o sistema de logs internos"""
    print("\n\n📊 Sistema de Logs Internos")
    print("=" * 40)
    
    # Criar gerenciador de logs
    log_manager = InternalLogManager()
    
    # Obter informações da sessão
    session_info = log_manager.get_session_info()
    print(f"🔑 Sessão: {session_info['session_id']}")
    print(f"📁 Diretório de logs: {session_info['log_dir']}")
    
    # Simular alguns logs
    print("\n🔄 Simulando eventos...")
    
    # Log de início de execução
    execution_id = f"exec_{int(time.time())}"
    log_manager.log_execution_start(
        execution_id,
        metadata={
            "workflow": "exemplo_releases",
            "user": "sistema",
            "version": "1.1.0"
        }
    )
    
    # Logs de tarefas
    tasks = ["init", "release", "backup", "cleanup"]
    for i, task in enumerate(tasks):
        log_manager.log_task_event(
            task,
            "started",
            metadata={"step": i+1, "total": len(tasks)}
        )
        
        time.sleep(0.1)  # Simular processamento
        
        log_manager.log_task_event(
            task,
            "completed",
            metadata={"step": i+1, "duration": 0.1}
        )
    
    # Log de performance
    log_manager.log_performance(
        "exemplo_completo",
        2.5,
        metadata={
            "tasks_count": len(tasks),
            "memory_usage": "15.2MB"
        }
    )
    
    # Log de auditoria
    log_manager.log_audit(
        "exemplo_executado",
        user="admin",
        metadata={
            "ip": "127.0.0.1",
            "timestamp": time.time()
        }
    )
    
    # Log de fim de execução
    log_manager.log_execution_end(
        execution_id,
        success=True,
        duration=2.5,
        metadata={
            "tasks_completed": len(tasks),
            "result": "sucesso"
        }
    )
    
    print("✅ Logs simulados gerados!")
    
    # Obter estatísticas
    print("\n📈 Estatísticas dos logs:")
    stats = log_manager.get_stats()
    print(f"   📝 Total de entradas: {stats['total_entries']}")
    
    if stats['levels']:
        print("   📊 Por nível:")
        for level, count in stats['levels'].items():
            print(f"      {level}: {count}")
    
    # Buscar logs
    print("\n🔍 Buscando logs recentes...")
    recent_logs = log_manager.search(limit=5)
    for log in recent_logs[-3:]:  # Últimos 3
        timestamp = log.get('timestamp', '')[-8:]  # HH:MM:SS
        level = log.get('level', '').ljust(7)
        message = log.get('message', '')[:50]
        print(f"   {timestamp} [{level}] {message}")
    
    return True


def exemplo_integracao_completa():
    """Demonstra integração completa dos sistemas"""
    print("\n\n🔗 Integração Completa")
    print("=" * 40)
    
    try:
        # 1. Criar checkpoint antes de mudanças
        backup_manager = BackupManager()
        checkpoint = backup_manager.create_checkpoint(
            name="pre_integration_test",
            description="Checkpoint antes do teste de integração"
        )
        print(f"🔖 Checkpoint criado: {checkpoint['name']}")
        
        # 2. Simular mudanças no código
        print("🔄 Simulando mudanças no projeto...")
        time.sleep(1)
        
        # 3. Criar novo release
        release_manager = ReleaseManager()
        release = release_manager.create_release(
            version="1.1.1",
            release_notes="Teste de integração dos sistemas de release, backup e logs"
        )
        print(f"🏷️ Release criado: {release['version']}")
        
        # 4. Criar backup após release
        backup = backup_manager.create_backup(
            name=f"release_{release['version']}_backup",
            description=f"Backup automático do release {release['version']}"
        )
        print(f"💾 Backup criado: {backup['name']}")
        
        # 5. Log da operação completa
        log_manager = InternalLogManager()
        log_manager.log_audit(
            "integracao_completa",
            user="sistema",
            metadata={
                "release": release['version'],
                "backup": backup['name'],
                "checkpoint": checkpoint['name']
            }
        )
        print("📊 Logs de auditoria registrados")
        
        print("\n✅ Integração completa executada com sucesso!")
        
        # Resumo final
        print("\n📋 Resumo:")
        print(f"   🏷️ Release: {release['version']}")
        print(f"   💾 Backup: {backup['name']}")
        print(f"   🔖 Checkpoint: {checkpoint['name']}")
        print(f"   📊 Logs: Registrados na sessão {log_manager.session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False


def main():
    """Função principal"""
    print("🎯 EXEMPLO: Sistema de Releases, Backups e Logs")
    print("=" * 60)
    
    try:
        # Executar exemplos
        if exemplo_sistema_releases():
            if exemplo_sistema_backups():
                if exemplo_sistema_logs():
                    exemplo_integracao_completa()
        
        print("\n" + "=" * 60)
        print("✨ Todos os exemplos executados com sucesso!")
        print("\n💡 Verifique os diretórios criados:")
        print("   📁 releases/ - Informações de releases")
        print("   📁 backups/ - Arquivos de backup") 
        print("   📁 logs/ - Logs estruturados")
        print("   📄 CHANGELOG.md - Histórico de mudanças")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 