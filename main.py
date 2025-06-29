#!/usr/bin/env python3
"""
Arquivo principal do Orquestrador
"""

import argparse
import sys
import time
from src import Orquestrador
from src.utils import load_config, setup_logger


def exemplo_simples():
    """Exemplo básico de uso do orquestrador"""
    print("🚀 Executando exemplo simples do Orquestrador")
    
    # Criar instância do orquestrador
    orq = Orquestrador(max_workers=2, log_level="INFO")
    
    # Definir algumas funções de exemplo
    def tarefa_inicial():
        print("📋 Executando tarefa inicial...")
        time.sleep(1)
        return "Tarefa inicial concluída"
    
    def processar_dados(dados="dados de exemplo"):
        print(f"⚙️ Processando: {dados}")
        time.sleep(2)
        return f"Dados processados: {dados}"
    
    def gerar_relatorio():
        print("📊 Gerando relatório...")
        time.sleep(1)
        return "Relatório gerado com sucesso"
    
    def enviar_notificacao():
        print("📧 Enviando notificação...")
        time.sleep(0.5)
        return "Notificação enviada"
    
    # Adicionar tarefas
    orq.add_task("inicio", tarefa_inicial)
    orq.add_task(
        "processar", 
        processar_dados,
        dependencies=["inicio"],
        dados="dados importantes"
    )
    orq.add_task(
        "relatorio",
        gerar_relatorio,
        dependencies=["processar"]
    )
    orq.add_task(
        "notificar",
        enviar_notificacao,
        dependencies=["relatorio"]
    )
    
    # Executar workflow
    print("\n📈 Iniciando execução do workflow...")
    resultados = orq.run(parallel=True)
    
    print("\n✅ Resultados:")
    for nome, resultado in resultados.items():
        print(f"  • {nome}: {resultado}")
    
    # Mostrar status final
    status = orq.get_status()
    print(f"\n📊 Status final:")
    print(f"  • Total de tarefas: {status['total_tasks']}")
    print(f"  • Tarefas concluídas: {status['completed_tasks']}")
    print(f"  • Tarefas com falha: {status['failed_tasks']}")


def executar_com_config(config_path: str):
    """Executa orquestrador com arquivo de configuração"""
    print(f"🔧 Carregando configuração de: {config_path}")
    
    try:
        config = load_config(config_path)
        print("✅ Configuração carregada com sucesso")
        
        # Criar orquestrador com configurações
        orq = Orquestrador(
            max_workers=config.get('max_workers', 4),
            log_level=config.get('log_level', 'INFO'),
            config=config
        )
        
        print("ℹ️ Configuração carregada. Implemente suas tarefas aqui!")
        
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        sys.exit(1)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Orquestrador - Sistema de orquestração de tarefas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                    # Executa exemplo simples
  python main.py -c config.yaml     # Usa arquivo de configuração
  python main.py --exemplo          # Executa exemplo demonstrativo
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Caminho para arquivo de configuração (YAML ou JSON)'
    )
    
    parser.add_argument(
        '--exemplo',
        action='store_true',
        help='Executa exemplo demonstrativo'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verboso (DEBUG)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging baseado nos argumentos
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logger("Main", log_level)
    
    try:
        if args.config:
            executar_com_config(args.config)
        else:
            exemplo_simples()
            
    except KeyboardInterrupt:
        logger.info("🛑 Execução interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 