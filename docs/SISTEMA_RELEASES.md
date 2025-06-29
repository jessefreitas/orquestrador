# Sistema de Releases, Backups e Logs

## Visão Geral

O Orquestrador agora possui um sistema completo de gestão de releases, backups e logs internos, proporcionando:

- **Versionamento Semântico**: Releases automatizados com controle de versão
- **Sistema de Backups**: Pontos de restauração completos e checkpoints rápidos
- **Logs Estruturados**: Sistema de logs internos com análise e auditoria
- **Automação**: Scripts e workflows para releases automatizados

## 🏷️ Sistema de Releases

### Funcionalidades

- **Versionamento Semântico**: Suporte a major.minor.patch[-pre-release][+build]
- **Metadados Completos**: Informações detalhadas de cada release
- **Changelog Automático**: Geração automática de histórico de mudanças
- **Integração Git**: Criação de tags e commits automatizados

### Uso Programático

```python
from src.version import ReleaseManager, get_version_info

# Informações de versão
version_info = get_version_info()
print(f"Versão atual: {version_info['version']}")

# Criar novo release
manager = ReleaseManager()
release = manager.create_release(
    version="1.2.0",
    release_notes="Nova versão com melhorias de performance",
    pre_release=False
)

# Listar releases
releases = manager.list_releases()
```

### CLI

```bash
# Criar release
python -m src.release_cli release create -v 1.2.0 -n "Nova versão"

# Listar releases
python -m src.release_cli release list

# Gerar changelog
python -m src.release_cli release changelog

# Informações de um release
python -m src.release_cli release info 1.2.0
```

## 💾 Sistema de Backups

### Tipos de Backup

1. **Backup Completo**: Arquivo ZIP com todos os arquivos importantes
2. **Checkpoint**: Snapshot rápido do estado atual (apenas metadados)

### Funcionalidades

- **Compressão**: Backups em formato ZIP para economia de espaço
- **Metadados**: Hash MD5, timestamps, informações de arquivos
- **Restauração**: Recuperação completa do estado do projeto
- **Limpeza Automática**: Remoção de checkpoints antigos
- **Backup de Segurança**: Criação automática antes de restaurações

### Uso Programático

```python
from src.backup import BackupManager

manager = BackupManager()

# Criar backup completo
backup = manager.create_backup(
    name="backup_v1_2_0",
    description="Backup da versão 1.2.0"
)

# Criar checkpoint
checkpoint = manager.create_checkpoint(
    name="pre_deploy",
    description="Antes do deploy"
)

# Restaurar backup
manager.restore_from_backup("backup_v1_2_0")

# Informações de armazenamento
storage = manager.get_storage_usage()
print(f"Total: {storage['total_size_mb']} MB")
```

### CLI

```bash
# Criar backup
python -m src.release_cli backup create -n "backup_importante" -d "Backup antes de mudanças"

# Listar backups
python -m src.release_cli backup list

# Restaurar backup
python -m src.release_cli backup restore backup_importante

# Criar checkpoint
python -m src.release_cli backup checkpoint -n "checkpoint_rapido"

# Informações de armazenamento
python -m src.release_cli backup storage
```

## 📊 Sistema de Logs Internos

### Tipos de Logs

1. **Logs Estruturados**: JSON Lines com metadados completos
2. **Logs de Auditoria**: Registro de ações importantes
3. **Logs de Performance**: Métricas de execução
4. **Logs de Sistema**: Eventos internos do sistema

### Funcionalidades

- **Formato JSON**: Logs estruturados para análise
- **Sessões**: Agrupamento por sessão de execução
- **Metadados**: Informações contextuais ricas
- **Rotação**: Rotação automática por tamanho e tempo
- **Análise**: Estatísticas e busca de logs
- **Exportação**: Exportação para análise externa

### Uso Programático

```python
from src.logging_system import InternalLogManager

log_manager = InternalLogManager()

# Log de execução
log_manager.log_execution_start("exec_001", {"user": "admin"})
log_manager.log_execution_end("exec_001", True, 2.5)

# Log de tarefa
log_manager.log_task_event("task_name", "started", {"priority": "high"})

# Log de performance
log_manager.log_performance("operation", 1.2, {"memory": "50MB"})

# Log de auditoria
log_manager.log_audit("user_login", "admin", {"ip": "192.168.1.1"})

# Buscar logs
results = log_manager.search(query="error", level="ERROR", limit=10)

# Estatísticas
stats = log_manager.get_stats()
```

### CLI

```bash
# Estatísticas dos logs
python -m src.release_cli logs stats

# Buscar logs
python -m src.release_cli logs search -q "error" -l ERROR --limit 10

# Exportar logs
python -m src.release_cli logs export logs_backup.json --start-date 2025-01-01

# Limpeza de logs
python -m src.release_cli logs cleanup
```

## 🤖 Automação

### Script de Release

```bash
# Release completo
python scripts/release.py 1.2.0 -n "Nova versão com melhorias"

# Release sem tag Git
python scripts/release.py 1.2.1 --no-tag

# Simulação (dry-run)
python scripts/release.py 1.3.0 --dry-run

# Pre-release
python scripts/release.py 1.3.0-beta --pre-release
```

### GitHub Actions

O projeto inclui workflow completo para releases automáticos:

- **Testes**: Execução em múltiplas versões do Python
- **Build**: Construção do pacote
- **Release**: Criação de release no GitHub
- **Publish**: Publicação no PyPI

## 📁 Estrutura de Diretórios

```
orquestrador/
├── releases/               # Informações de releases
│   ├── releases.json      # Histórico de releases
│   └── v1.2.0/           # Dados específicos do release
├── backups/               # Sistema de backups
│   ├── backup_metadata.json # Metadados dos backups
│   ├── checkpoints/       # Checkpoints rápidos
│   └── backup_v1_2_0/    # Backup completo
├── logs/                  # Logs internos
│   ├── orquestrador_structured.jsonl
│   ├── audit.log
│   ├── performance.jsonl
│   └── system.jsonl
└── scripts/               # Scripts de automação
    └── release.py
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Configurações opcionais
export ORQUESTRADOR_LOG_LEVEL=DEBUG
export ORQUESTRADOR_BACKUP_DIR=/path/to/backups
export ORQUESTRADOR_LOG_DIR=/path/to/logs
```

### Integração com CI/CD

Para integrar com pipelines de CI/CD:

1. **Instalar dependências**: `pip install -r requirements.txt`
2. **Executar testes**: `python -m pytest tests/`
3. **Criar release**: `python scripts/release.py $VERSION`
4. **Criar backup**: `python -c "from src.backup import BackupManager; BackupManager().create_backup()"`

## 📈 Monitoramento

### Métricas Disponíveis

- **Releases**: Quantidade, frequência, tamanho
- **Backups**: Uso de armazenamento, frequência
- **Logs**: Volume, erros, performance
- **Sistema**: Uso de recursos, sessões ativas

### Dashboards

Use as APIs de estatísticas para criar dashboards:

```python
# Métricas de releases
release_manager = ReleaseManager()
releases = release_manager.list_releases()

# Métricas de backups
backup_manager = BackupManager()
storage = backup_manager.get_storage_usage()

# Métricas de logs
log_manager = InternalLogManager()
stats = log_manager.get_stats()
```

## 🚀 Próximos Passos

1. **Integração com Banco de Dados**: Armazenar metadados em BD
2. **Interface Web**: Dashboard para gestão visual
3. **Alertas**: Notificações para eventos importantes
4. **Integração Externa**: Webhooks e APIs REST
5. **Relatórios**: Relatórios periódicos automáticos

## 🔗 Referências

- [Versionamento Semântico](https://semver.org/)
- [Structured Logging](https://structlog.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Python Packaging](https://packaging.python.org/)

---

*Sistema implementado em 29/06/2025 - Versão 1.1.0* 