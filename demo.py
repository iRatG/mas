#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрационный скрипт для показа возможностей MAS системы.
"""

import asyncio
import subprocess
import time

def run_command(cmd, description):
    """Запуск команды с описанием."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"Команда: {cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print("Ошибки:", result.stderr)
    
    time.sleep(1)  # Небольшая пауза между демо

def main():
    """Демонстрация возможностей системы."""
    
    print("🎯 ДЕМОНСТРАЦИЯ MAS СИСТЕМЫ")
    print("Система для автоматического исправления багов с двумя подходами")
    
    demos = [
        ("python main.py --help", 
         "Справка по доступным параметрам"),
        
        ("python main.py --approach sync --cases 1 2", 
         "Синхронный подход на кейсах 1-2"),
        
        ("python main.py --approach async --cases 1", 
         "Асинхронный подход на кейсе 1"),
        
        ("python main.py --approach both --cases 3 --save-results demo_results.json", 
         "Сравнение подходов с сохранением результатов"),
        
        ("python main.py --approach async --parallel --cases 1 2 3", 
         "Асинхронный подход в параллельном режиме"),
    ]
    
    for cmd, desc in demos:
        try:
            run_command(cmd, desc)
        except KeyboardInterrupt:
            print("\n⏹️ Демонстрация прервана пользователем")
            break
        except Exception as e:
            print(f"❌ Ошибка при выполнении команды: {e}")
    
    print(f"\n{'='*60}")
    print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("Проверьте файл demo_results.json для детальных результатов")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
