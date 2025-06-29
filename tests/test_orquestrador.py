#!/usr/bin/env python3
"""
Testes para o Orquestrador
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import Orquestrador, Task, TaskStatus


class TestTask(unittest.TestCase):
    """Testes para a classe Task"""
    
    def test_task_creation(self):
        """Testa criação de tarefa"""
        def exemplo_func():
            return "resultado"
        
        task = Task("teste", exemplo_func, description="Tarefa de teste")
        
        self.assertEqual(task.name, "teste")
        self.assertEqual(task.description, "Tarefa de teste")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.dependencies, [])
        self.assertEqual(task.retry_count, 0)
    
    def test_task_execution(self):
        """Testa execução de tarefa"""
        def exemplo_func():
            return "sucesso"
        
        task = Task("teste", exemplo_func)
        resultado = task.execute()
        
        self.assertEqual(resultado, "sucesso")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.result, "sucesso")
        self.assertIsNotNone(task.start_time)
        self.assertIsNotNone(task.end_time)
        self.assertIsNotNone(task.duration)
    
    def test_task_execution_failure(self):
        """Testa falha na execução de tarefa"""
        def exemplo_func():
            raise ValueError("Erro simulado")
        
        task = Task("teste", exemplo_func)
        
        with self.assertRaises(ValueError):
            task.execute()
        
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIsNotNone(task.error)
    
    def test_task_with_arguments(self):
        """Testa tarefa com argumentos"""
        def exemplo_func(x, y=10):
            return x + y
        
        task = Task("teste", exemplo_func, x=5, y=15)
        resultado = task.execute()
        
        self.assertEqual(resultado, 20)
    
    def test_task_reset(self):
        """Testa reset de tarefa"""
        def exemplo_func():
            return "resultado"
        
        task = Task("teste", exemplo_func)
        task.execute()
        
        # Verificar que está executada
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        
        # Reset
        task.reset()
        
        # Verificar que foi resetada
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.start_time)
        self.assertIsNone(task.end_time)
        self.assertIsNone(task.result)
        self.assertIsNone(task.error)


class TestOrquestrador(unittest.TestCase):
    """Testes para a classe Orquestrador"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.orq = Orquestrador(max_workers=2, log_level="ERROR")  # ERROR para reduzir logs
    
    def test_orquestrador_creation(self):
        """Testa criação do orquestrador"""
        self.assertEqual(self.orq.max_workers, 2)
        self.assertEqual(len(self.orq.tasks), 0)
        self.assertFalse(self.orq.is_running)
    
    def test_add_task(self):
        """Testa adição de tarefa"""
        def exemplo_func():
            return "resultado"
        
        task = self.orq.add_task("teste", exemplo_func)
        
        self.assertIn("teste", self.orq.tasks)
        self.assertEqual(task.name, "teste")
        self.assertEqual(len(self.orq.list_tasks()), 1)
    
    def test_add_duplicate_task(self):
        """Testa erro ao adicionar tarefa duplicada"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("teste", exemplo_func)
        
        with self.assertRaises(ValueError):
            self.orq.add_task("teste", exemplo_func)
    
    def test_remove_task(self):
        """Testa remoção de tarefa"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("teste", exemplo_func)
        self.assertEqual(len(self.orq.tasks), 1)
        
        self.orq.remove_task("teste")
        self.assertEqual(len(self.orq.tasks), 0)
    
    def test_remove_nonexistent_task(self):
        """Testa erro ao remover tarefa inexistente"""
        with self.assertRaises(ValueError):
            self.orq.remove_task("inexistente")
    
    def test_remove_task_with_dependents(self):
        """Testa erro ao remover tarefa com dependentes"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("pai", exemplo_func)
        self.orq.add_task("filho", exemplo_func, dependencies=["pai"])
        
        with self.assertRaises(ValueError):
            self.orq.remove_task("pai")
    
    def test_get_task(self):
        """Testa busca de tarefa"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("teste", exemplo_func)
        task = self.orq.get_task("teste")
        
        self.assertEqual(task.name, "teste")
    
    def test_get_nonexistent_task(self):
        """Testa erro ao buscar tarefa inexistente"""
        with self.assertRaises(ValueError):
            self.orq.get_task("inexistente")
    
    def test_validate_dependencies(self):
        """Testa validação de dependências"""
        def exemplo_func():
            return "resultado"
        
        # Dependência válida
        self.orq.add_task("pai", exemplo_func)
        self.orq.add_task("filho", exemplo_func, dependencies=["pai"])
        
        errors = self.orq.validate()
        self.assertEqual(len(errors), 0)
        
        # Dependência inválida
        self.orq.add_task("orfao", exemplo_func, dependencies=["inexistente"])
        
        errors = self.orq.validate()
        self.assertGreater(len(errors), 0)
    
    def test_plan_execution(self):
        """Testa planejamento de execução"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("a", exemplo_func)
        self.orq.add_task("b", exemplo_func, dependencies=["a"])
        self.orq.add_task("c", exemplo_func, dependencies=["b"])
        
        order = self.orq.plan_execution()
        
        self.assertEqual(order, ["a", "b", "c"])
    
    def test_plan_execution_with_parallel_tasks(self):
        """Testa planejamento com tarefas paralelas"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("inicio", exemplo_func)
        self.orq.add_task("paralela1", exemplo_func, dependencies=["inicio"])
        self.orq.add_task("paralela2", exemplo_func, dependencies=["inicio"])
        self.orq.add_task("fim", exemplo_func, dependencies=["paralela1", "paralela2"])
        
        order = self.orq.plan_execution()
        
        # Início deve ser primeiro, fim deve ser último
        self.assertEqual(order[0], "inicio")
        self.assertEqual(order[-1], "fim")
        
        # Paralelas devem estar no meio
        self.assertIn("paralela1", order[1:3])
        self.assertIn("paralela2", order[1:3])
    
    def test_run_sequential(self):
        """Testa execução sequencial"""
        resultados_esperados = []
        
        def criar_func(nome):
            def func():
                resultados_esperados.append(nome)
                time.sleep(0.1)
                return f"resultado_{nome}"
            return func
        
        self.orq.add_task("a", criar_func("a"))
        self.orq.add_task("b", criar_func("b"), dependencies=["a"])
        self.orq.add_task("c", criar_func("c"), dependencies=["b"])
        
        resultados = self.orq.run(parallel=False)
        
        # Verificar resultados
        self.assertEqual(len(resultados), 3)
        self.assertEqual(resultados["a"], "resultado_a")
        self.assertEqual(resultados["b"], "resultado_b")
        self.assertEqual(resultados["c"], "resultado_c")
        
        # Verificar ordem de execução
        self.assertEqual(resultados_esperados, ["a", "b", "c"])
    
    def test_run_parallel(self):
        """Testa execução paralela"""
        def exemplo_func(nome):
            time.sleep(0.1)
            return f"resultado_{nome}"
        
        self.orq.add_task("inicio", lambda: exemplo_func("inicio"))
        self.orq.add_task("paralela1", lambda: exemplo_func("paralela1"), dependencies=["inicio"])
        self.orq.add_task("paralela2", lambda: exemplo_func("paralela2"), dependencies=["inicio"])
        
        resultados = self.orq.run(parallel=True)
        
        self.assertEqual(len(resultados), 3)
        self.assertEqual(resultados["inicio"], "resultado_inicio")
        self.assertEqual(resultados["paralela1"], "resultado_paralela1")
        self.assertEqual(resultados["paralela2"], "resultado_paralela2")
    
    def test_run_with_failure(self):
        """Testa execução com falha"""
        def exemplo_func():
            return "sucesso"
        
        def func_falha():
            raise ValueError("Erro simulado")
        
        self.orq.add_task("sucesso", exemplo_func)
        self.orq.add_task("falha", func_falha, dependencies=["sucesso"])
        
        with self.assertRaises(ValueError):
            self.orq.run()
    
    def test_run_with_retry(self):
        """Testa execução com retry"""
        contador = {"valor": 0}
        
        def func_instavel():
            contador["valor"] += 1
            if contador["valor"] < 3:
                raise ValueError("Falha temporária")
            return "sucesso na terceira tentativa"
        
        self.orq.add_task("instavel", func_instavel, retry_count=3)
        
        resultados = self.orq.run()
        
        self.assertEqual(resultados["instavel"], "sucesso na terceira tentativa")
        self.assertEqual(contador["valor"], 3)
    
    def test_get_status(self):
        """Testa obtenção de status"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("teste", exemplo_func)
        
        # Status inicial
        status = self.orq.get_status()
        self.assertFalse(status["is_running"])
        self.assertEqual(status["total_tasks"], 1)
        self.assertEqual(status["completed_tasks"], 0)
        
        # Após execução
        self.orq.run()
        status = self.orq.get_status()
        self.assertFalse(status["is_running"])
        self.assertEqual(status["completed_tasks"], 1)
        self.assertEqual(status["failed_tasks"], 0)
    
    def test_reset(self):
        """Testa reset do orquestrador"""
        def exemplo_func():
            return "resultado"
        
        self.orq.add_task("teste", exemplo_func)
        self.orq.run()
        
        # Verificar que executou
        self.assertEqual(len(self.orq.results), 1)
        
        # Reset
        self.orq.reset()
        
        # Verificar que foi resetado
        self.assertEqual(len(self.orq.results), 0)
        self.assertIsNone(self.orq.start_time)
        self.assertIsNone(self.orq.end_time)
        
        # Tarefas devem estar resetadas
        task = self.orq.get_task("teste")
        self.assertEqual(task.status, TaskStatus.PENDING)


class TestUtils(unittest.TestCase):
    """Testes para utilitários"""
    
    def test_topological_sort(self):
        """Testa ordenação topológica"""
        from src.utils import topological_sort
        
        # Criar mock de tarefas
        tasks = {
            "a": Mock(dependencies=[]),
            "b": Mock(dependencies=["a"]),
            "c": Mock(dependencies=["b"]),
            "d": Mock(dependencies=["a"]),
        }
        
        order = topological_sort(tasks)
        
        # 'a' deve vir primeiro
        self.assertEqual(order[0], "a")
        
        # 'b' e 'd' devem vir depois de 'a'
        a_index = order.index("a")
        b_index = order.index("b")
        d_index = order.index("d")
        
        self.assertGreater(b_index, a_index)
        self.assertGreater(d_index, a_index)
        
        # 'c' deve vir depois de 'b'
        c_index = order.index("c")
        self.assertGreater(c_index, b_index)
    
    def test_format_duration(self):
        """Testa formatação de duração"""
        from src.utils import format_duration
        
        self.assertEqual(format_duration(30), "30.00s")
        self.assertEqual(format_duration(90), "1m 30.00s")
        self.assertEqual(format_duration(3665), "1h 1m 5.00s")


if __name__ == "__main__":
    print("🧪 Executando testes do Orquestrador...")
    unittest.main(verbosity=2) 