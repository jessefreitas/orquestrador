#!/usr/bin/env python3
"""
Exemplo básico de uso do Orquestrador
"""

import sys
import os
import time

# Adicionar o diretório pai ao path para importar o módulo src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import Orquestrador


def exemplo_pipeline_dados():
    """
    Exemplo de pipeline de processamento de dados
    """
    print("🔄 Exemplo: Pipeline de Processamento de Dados")
    print("=" * 50)
    
    # Criar orquestrador
    orq = Orquestrador(max_workers=3, log_level="INFO")
    
    # === Definir funções das tarefas ===
    
    def extrair_dados():
        """Simula extração de dados de uma fonte"""
        print("📥 Extraindo dados da fonte...")
        time.sleep(1)
        dados = {
            "usuarios": 1500,
            "vendas": 2800,
            "produtos": 150
        }
        print(f"✅ Dados extraídos: {dados}")
        return dados
    
    def validar_dados(dados):
        """Valida os dados extraídos"""
        print("🔍 Validando dados...")
        time.sleep(0.5)
        
        # Simulação de validação
        if not dados or len(dados) == 0:
            raise ValueError("Dados vazios!")
        
        print("✅ Dados válidos")
        return {"status": "válido", "dados": dados}
    
    def transformar_dados(resultado_validacao):
        """Transforma os dados"""
        print("⚙️ Transformando dados...")
        time.sleep(1.5)
        
        dados = resultado_validacao["dados"]
        dados_transformados = {
            "total_usuarios": dados["usuarios"],
            "receita_total": dados["vendas"] * 50,  # Assumindo R$ 50 por venda
            "produtos_ativos": dados["produtos"]
        }
        
        print(f"✅ Dados transformados: {dados_transformados}")
        return dados_transformados
    
    def gerar_relatorio(dados_transformados):
        """Gera relatório final"""
        print("📊 Gerando relatório...")
        time.sleep(1)
        
        relatorio = f"""
        📈 RELATÓRIO DE DADOS
        {'=' * 30}
        👥 Total de Usuários: {dados_transformados['total_usuarios']:,}
        💰 Receita Total: R$ {dados_transformados['receita_total']:,}
        📦 Produtos Ativos: {dados_transformados['produtos_ativos']}
        
        📅 Data: {time.strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        print("✅ Relatório gerado")
        return relatorio
    
    def enviar_email():
        """Simula envio de email"""
        print("📧 Enviando relatório por email...")
        time.sleep(0.5)
        print("✅ Email enviado com sucesso")
        return "Email enviado para: admin@empresa.com"
    
    def backup_dados(dados_transformados):
        """Faz backup dos dados"""
        print("💾 Fazendo backup dos dados...")
        time.sleep(0.8)
        backup_id = f"backup_{int(time.time())}"
        print(f"✅ Backup realizado: {backup_id}")
        return backup_id
    
    # === Adicionar tarefas ao orquestrador ===
    
    # Tarefa inicial - extração
    orq.add_task(
        "extrair",
        extrair_dados,
        description="Extrai dados da fonte principal"
    )
    
    # Variáveis para armazenar resultados temporariamente
    dados_extraidos = None
    dados_validados = None
    dados_transformados = None
    
    def validar_wrapper():
        nonlocal dados_validados
        dados_validados = validar_dados(dados_extraidos)
        return dados_validados
    
    def transformar_wrapper():
        nonlocal dados_transformados
        dados_transformados = transformar_dados(dados_validados)
        return dados_transformados
    
    def relatorio_wrapper():
        return gerar_relatorio(dados_transformados)
    
    def backup_wrapper():
        return backup_dados(dados_transformados)
    
    # Modificar a função de extração para salvar resultado
    def extrair_dados_wrapper():
        nonlocal dados_extraidos
        dados_extraidos = extrair_dados()
        return dados_extraidos
    
    # Atualizar tarefa de extração
    orq.tasks["extrair"].function = extrair_dados_wrapper
    
    # Validação - depende da extração
    orq.add_task(
        "validar",
        validar_wrapper,
        dependencies=["extrair"],
        description="Valida os dados extraídos"
    )
    
    # Transformação - depende da validação
    orq.add_task(
        "transformar",
        transformar_wrapper,
        dependencies=["validar"],
        description="Transforma e processa os dados"
    )
    
    # Relatório - depende da transformação
    orq.add_task(
        "relatorio",
        relatorio_wrapper,
        dependencies=["transformar"],
        description="Gera relatório final"
    )
    
    # Tarefas paralelas que dependem da transformação
    orq.add_task(
        "email",
        enviar_email,
        dependencies=["relatorio"],
        description="Envia relatório por email"
    )
    
    orq.add_task(
        "backup",
        backup_wrapper,
        dependencies=["transformar"],
        description="Faz backup dos dados processados"
    )
    
    # === Executar pipeline ===
    
    print("\n🚀 Iniciando execução do pipeline...")
    print("Ordem das tarefas será calculada automaticamente baseada nas dependências\n")
    
    try:
        # Executar com paralelismo habilitado
        resultados = orq.run(parallel=True)
        
        print("\n" + "=" * 50)
        print("🎉 PIPELINE CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        
        # Mostrar resultados
        print("\n📋 Resultados:")
        for nome, resultado in resultados.items():
            print(f"\n🔸 {nome.upper()}:")
            if isinstance(resultado, dict):
                for k, v in resultado.items():
                    print(f"   {k}: {v}")
            elif isinstance(resultado, str) and len(resultado) > 100:
                print(f"   {resultado[:100]}...")
            else:
                print(f"   {resultado}")
        
        # Status final
        status = orq.get_status()
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   ⏱️ Início: {status['start_time']}")
        print(f"   ⏱️ Fim: {status['end_time']}")
        print(f"   ✅ Tarefas concluídas: {status['completed_tasks']}/{status['total_tasks']}")
        print(f"   ❌ Tarefas com falha: {status['failed_tasks']}")
        
        # Duração de cada tarefa
        print(f"\n⏱️ DURAÇÃO DAS TAREFAS:")
        for nome, info in status['tasks'].items():
            duration = info['duration']
            if duration:
                print(f"   {nome}: {duration:.2f}s")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        return False
    
    return True


def exemplo_com_falha():
    """
    Exemplo demonstrando tratamento de falhas e retry
    """
    print("\n\n🔄 Exemplo: Tratamento de Falhas")
    print("=" * 50)
    
    orq = Orquestrador(max_workers=2, log_level="INFO")
    
    # Contador para simular falha intermitente
    contador_tentativas = {"valor": 0}
    
    def tarefa_instavel():
        """Tarefa que falha nas primeiras tentativas"""
        contador_tentativas["valor"] += 1
        print(f"🎯 Tentativa {contador_tentativas['valor']}")
        
        if contador_tentativas["valor"] < 3:
            raise Exception(f"Falha simulada (tentativa {contador_tentativas['valor']})")
        
        print("✅ Sucesso na terceira tentativa!")
        return "Tarefa concluída com retry"
    
    def tarefa_dependente():
        """Tarefa que depende da instável"""
        print("🎯 Executando tarefa dependente...")
        time.sleep(0.5)
        return "Tarefa dependente concluída"
    
    # Adicionar tarefas
    orq.add_task(
        "instavel",
        tarefa_instavel,
        retry_count=3,  # 3 tentativas
        description="Tarefa que falha intermitentemente"
    )
    
    orq.add_task(
        "dependente",
        tarefa_dependente,
        dependencies=["instavel"],
        description="Tarefa que depende da instável"
    )
    
    print("\n🚀 Executando exemplo com retry...")
    
    try:
        resultados = orq.run()
        print("\n✅ Exemplo concluído com sucesso!")
        print("📋 Resultados:")
        for nome, resultado in resultados.items():
            print(f"   {nome}: {resultado}")
            
    except Exception as e:
        print(f"\n❌ Falha final: {e}")


if __name__ == "__main__":
    print("🎯 EXEMPLOS DO ORQUESTRADOR")
    print("=" * 60)
    
    # Executar exemplo principal
    sucesso = exemplo_pipeline_dados()
    
    if sucesso:
        # Executar exemplo com falha
        exemplo_com_falha()
    
    print("\n" + "=" * 60)
    print("✨ Exemplos concluídos! Verifique os logs gerados em logs/")
    print("💡 Para mais exemplos, consulte a documentação no README.md") 