"""
Interface CLI para gerenciamento de releases, backups e logs
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from .version import ReleaseManager, get_version_info
from .backup import BackupManager
from .logging_system import InternalLogManager


@click.group()
@click.version_option()
def cli():
    """Orquestrador Release Manager - Gerenciamento de versões, backups e logs"""
    pass


@cli.group()
def release():
    """Comandos de gerenciamento de releases"""
    pass


@cli.group()
def backup():
    """Comandos de gerenciamento de backups"""
    pass


@cli.group()
def logs():
    """Comandos de gerenciamento de logs"""
    pass


# === COMANDOS DE RELEASE ===

@release.command()
@click.option('--version', '-v', help='Versão do release (auto-incrementa se não especificado)')
@click.option('--notes', '-n', default='', help='Notas do release')
@click.option('--pre-release', is_flag=True, help='Marcar como pre-release')
def create(version, notes, pre_release):
    """Criar um novo release"""
    try:
        manager = ReleaseManager()
        release_info = manager.create_release(
            version=version,
            release_notes=notes,
            pre_release=pre_release
        )
        
        click.echo(f"✅ Release {release_info['version']} criado com sucesso!")
        click.echo(f"📅 Data: {release_info['release_date']}")
        click.echo(f"📄 Notas: {notes or 'Sem notas'}")
        
    except Exception as e:
        click.echo(f"❌ Erro ao criar release: {e}", err=True)
        sys.exit(1)


@release.command()
def list():
    """Listar todos os releases"""
    try:
        manager = ReleaseManager()
        releases = manager.list_releases()
        
        if not releases:
            click.echo("📭 Nenhum release encontrado")
            return
        
        click.echo("📋 Releases disponíveis:\n")
        for release in reversed(releases):
            version = release['version']
            date = release['release_date'][:10]
            pre = " (Pre-release)" if release.get('pre_release') else ""
            
            click.echo(f"🏷️  {version}{pre}")
            click.echo(f"   📅 {date}")
            if release.get('release_notes'):
                click.echo(f"   📄 {release['release_notes'][:60]}...")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Erro ao listar releases: {e}", err=True)


@release.command()
@click.argument('version')
def info(version):
    """Mostrar informações de um release específico"""
    try:
        manager = ReleaseManager()
        release = manager.get_release(version)
        
        if not release:
            click.echo(f"❌ Release {version} não encontrado")
            sys.exit(1)
        
        click.echo(f"📦 Release {release['version']}")
        click.echo(f"📅 Data: {release['release_date']}")
        click.echo(f"🔧 Build: {release['build_info']['build_number']}")
        click.echo(f"📄 Notas: {release.get('release_notes', 'Sem notas')}")
        click.echo(f"📊 Arquivos: {len(release['files'])} itens")
        
    except Exception as e:
        click.echo(f"❌ Erro ao obter informações: {e}", err=True)


@release.command()
def changelog():
    """Gerar changelog dos releases"""
    try:
        manager = ReleaseManager()
        changelog_content = manager.create_changelog()
        
        # Salvar em arquivo
        changelog_file = Path("CHANGELOG.md")
        with open(changelog_file, 'w', encoding='utf-8') as f:
            f.write(changelog_content)
        
        click.echo(f"✅ Changelog gerado em: {changelog_file}")
        click.echo("\n📄 Prévia:")
        click.echo(changelog_content[:500] + "..." if len(changelog_content) > 500 else changelog_content)
        
    except Exception as e:
        click.echo(f"❌ Erro ao gerar changelog: {e}", err=True)


# === COMANDOS DE BACKUP ===

@backup.command()
@click.option('--name', '-n', help='Nome do backup')
@click.option('--description', '-d', default='', help='Descrição do backup')
def create(name, description):
    """Criar um backup completo"""
    try:
        manager = BackupManager()
        
        click.echo("🔄 Criando backup...")
        backup_info = manager.create_backup(name=name, description=description)
        
        size_mb = backup_info['size'] / (1024 * 1024)
        click.echo(f"✅ Backup '{backup_info['name']}' criado com sucesso!")
        click.echo(f"📦 Tamanho: {size_mb:.2f} MB")
        click.echo(f"📅 Data: {backup_info['timestamp']}")
        
    except Exception as e:
        click.echo(f"❌ Erro ao criar backup: {e}", err=True)
        sys.exit(1)


@backup.command()
def list():
    """Listar todos os backups"""
    try:
        manager = BackupManager()
        backups = manager.list_backups()
        
        if not backups:
            click.echo("📭 Nenhum backup encontrado")
            return
        
        click.echo("💾 Backups disponíveis:\n")
        for backup in reversed(backups):
            name = backup['name']
            date = backup['timestamp'][:10]
            size_mb = backup['size'] / (1024 * 1024)
            
            click.echo(f"📦 {name}")
            click.echo(f"   📅 {date}")
            click.echo(f"   📊 {size_mb:.2f} MB")
            if backup.get('description'):
                click.echo(f"   📄 {backup['description']}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Erro ao listar backups: {e}", err=True)


@backup.command()
@click.argument('backup_name')
@click.confirmation_option(prompt='Tem certeza que deseja restaurar este backup?')
def restore(backup_name):
    """Restaurar um backup"""
    try:
        manager = BackupManager()
        
        click.echo(f"🔄 Restaurando backup '{backup_name}'...")
        success = manager.restore_from_backup(backup_name)
        
        if success:
            click.echo("✅ Backup restaurado com sucesso!")
        else:
            click.echo("❌ Falha na restauração")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Erro ao restaurar backup: {e}", err=True)
        sys.exit(1)


@backup.command()
@click.option('--name', '-n', help='Nome do checkpoint')
@click.option('--description', '-d', default='', help='Descrição do checkpoint')
def checkpoint(name, description):
    """Criar um checkpoint rápido"""
    try:
        manager = BackupManager()
        
        checkpoint_info = manager.create_checkpoint(name=name, description=description)
        
        click.echo(f"✅ Checkpoint '{checkpoint_info['name']}' criado!")
        click.echo(f"📅 Data: {checkpoint_info['timestamp']}")
        
    except Exception as e:
        click.echo(f"❌ Erro ao criar checkpoint: {e}", err=True)


@backup.command()
def storage():
    """Mostrar uso de armazenamento"""
    try:
        manager = BackupManager()
        usage = manager.get_storage_usage()
        
        click.echo("💽 Uso de Armazenamento:")
        click.echo(f"📦 Backups: {usage['backup_count']}")
        click.echo(f"🔖 Checkpoints: {usage['checkpoint_count']}")
        click.echo(f"📊 Tamanho total: {usage['total_size_mb']} MB")
        click.echo(f"📁 Diretório: {usage['backup_dir']}")
        
    except Exception as e:
        click.echo(f"❌ Erro ao obter informações: {e}", err=True)


# === COMANDOS DE LOGS ===

@logs.command()
def stats():
    """Mostrar estatísticas dos logs"""
    try:
        log_manager = InternalLogManager()
        stats = log_manager.get_stats()
        
        click.echo("📊 Estatísticas dos Logs:")
        click.echo(f"📝 Total de entradas: {stats['total_entries']}")
        
        if stats['levels']:
            click.echo("\n📈 Por nível:")
            for level, count in stats['levels'].items():
                click.echo(f"   {level}: {count}")
        
        if stats['time_range']['start']:
            click.echo(f"\n⏰ Período: {stats['time_range']['start']} até {stats['time_range']['end']}")
        
        if stats['errors']:
            click.echo(f"\n❌ Erros: {len(stats['errors'])}")
        
        if stats['warnings']:
            click.echo(f"⚠️ Warnings: {len(stats['warnings'])}")
            
    except Exception as e:
        click.echo(f"❌ Erro ao obter estatísticas: {e}", err=True)


@logs.command()
@click.option('--query', '-q', help='Texto para buscar')
@click.option('--level', '-l', help='Nível de log (INFO, ERROR, etc.)')
@click.option('--limit', default=10, help='Número máximo de resultados')
def search(query, level, limit):
    """Buscar logs"""
    try:
        log_manager = InternalLogManager()
        results = log_manager.search(
            query=query,
            level=level,
            limit=limit
        )
        
        if not results:
            click.echo("📭 Nenhum log encontrado")
            return
        
        click.echo(f"🔍 {len(results)} logs encontrados:\n")
        for entry in results:
            timestamp = entry.get('timestamp', '')[11:19]  # HH:MM:SS
            level = entry.get('level', '').ljust(7)
            message = entry.get('message', '')[:60]
            
            click.echo(f"{timestamp} [{level}] {message}")
            
    except Exception as e:
        click.echo(f"❌ Erro na busca: {e}", err=True)


@logs.command()
@click.argument('output_file')
@click.option('--start-date', help='Data inicial (YYYY-MM-DD)')
@click.option('--end-date', help='Data final (YYYY-MM-DD)')
def export(output_file, start_date, end_date):
    """Exportar logs para arquivo"""
    try:
        log_manager = InternalLogManager()
        
        count = log_manager.export_logs(
            output_file,
            start_date=start_date,
            end_date=end_date
        )
        
        click.echo(f"✅ {count} logs exportados para: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Erro na exportação: {e}", err=True)


@logs.command()
def cleanup():
    """Limpar logs antigos"""
    try:
        log_manager = InternalLogManager()
        
        click.echo("🧹 Limpando logs antigos...")
        log_manager.cleanup_old_logs(days=30)
        log_manager.compress_old_logs()
        
        click.echo("✅ Limpeza concluída!")
        
    except Exception as e:
        click.echo(f"❌ Erro na limpeza: {e}", err=True)


# === COMANDO PRINCIPAL DE INFORMAÇÕES ===

@cli.command()
def info():
    """Mostrar informações do sistema"""
    try:
        version_info = get_version_info()
        
        click.echo("🎯 Orquestrador - Sistema de Orquestração")
        click.echo("=" * 40)
        click.echo(f"📦 Versão: {version_info['version']}")
        click.echo(f"🏗️ Build: {version_info['build']}")
        click.echo(f"📅 Data de release: {version_info['release_date']}")
        click.echo(f"🐍 Python: {version_info['python_version'].split()[0]}")
        click.echo(f"💻 Plataforma: {version_info['platform']}")
        
        # Informações de backup
        backup_manager = BackupManager()
        storage = backup_manager.get_storage_usage()
        
        click.echo("\n💾 Backups:")
        click.echo(f"   📦 {storage['backup_count']} backups")
        click.echo(f"   🔖 {storage['checkpoint_count']} checkpoints")
        click.echo(f"   📊 {storage['total_size_mb']} MB")
        
        # Informações de logs
        log_manager = InternalLogManager()
        log_stats = log_manager.get_stats()
        
        click.echo("\n📊 Logs:")
        click.echo(f"   📝 {log_stats['total_entries']} entradas")
        if log_stats['errors']:
            click.echo(f"   ❌ {len(log_stats['errors'])} erros")
        if log_stats['warnings']:
            click.echo(f"   ⚠️ {len(log_stats['warnings'])} warnings")
        
    except Exception as e:
        click.echo(f"❌ Erro ao obter informações: {e}", err=True)


if __name__ == '__main__':
    cli() 