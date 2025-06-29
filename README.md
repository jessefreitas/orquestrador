# Orquestrador

Sistema de orquestração de tarefas e processos automatizados.

## Descrição

O Orquestrador é uma ferramenta para coordenar e executar tarefas de forma sequencial ou paralela, permitindo a criação de workflows automatizados com controle de dependências e monitoramento de execução.

## Funcionalidades

- ✅ Execução de tarefas sequenciais
- ✅ Execução de tarefas paralelas  
- ✅ Gerenciamento de dependências entre tarefas
- ✅ Sistema de logs detalhado
- ✅ Configuração via arquivo JSON/YAML
- ✅ Monitoramento de status de execução

## Instalação

```bash
git clone https://github.com/jessefreitas/orquestrador.git
cd orquestrador
pip install -r requirements.txt
```

## Uso Básico

```python
from src.orquestrador import Orquestrador

# Criar instância do orquestrador
orq = Orquestrador()

# Adicionar tarefas
orq.add_task("tarefa1", lambda: print("Executando tarefa 1"))
orq.add_task("tarefa2", lambda: print("Executando tarefa 2"), dependencies=["tarefa1"])

# Executar workflow
orq.run()
```

## Estrutura do Projeto

```
orquestrador/
├── src/                    # Código fonte
│   ├── orquestrador.py    # Classe principal
│   ├── task.py            # Definição de tarefas
│   └── utils.py           # Utilitários
├── config/                # Arquivos de configuração
├── logs/                  # Logs de execução
├── examples/              # Exemplos de uso
├── tests/                 # Testes
├── main.py               # Arquivo principal
├── requirements.txt      # Dependências
└── README.md            # Documentação
```

## Configuração

As configurações podem ser definidas em `config/config.yaml` ou passadas diretamente na inicialização.

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Autor

Jesse Freitas - [@jessefreitas](https://github.com/jessefreitas) 