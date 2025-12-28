import requests
import json
import sys
from typing import Dict, Any, List


class TodoAPIClient:
    """Клиент для работы с API управления задачами."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def create_task(self, title: str, priority: str = "normal") -> Dict[str, Any]:
        """Создает новую задачу."""
        url = f"{self.base_url}/tasks"
        data = {"title": title, "priority": priority}
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка: {e}")
            return {}
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Получает все задачи."""
        url = f"{self.base_url}/tasks"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка: {e}")
            return []
    
    def mark_task_complete(self, task_id: int) -> bool:
        """Отмечает задачу как выполненную."""
        url = f"{self.base_url}/tasks/{task_id}/complete"
        
        try:
            response = self.session.post(url)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """Удаляет задачу."""
        url = f"{self.base_url}/tasks/{task_id}"
        
        try:
            response = self.session.delete(url)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def clear_all_tasks(self):
        """Удаляет все задачи."""
        tasks = self.get_all_tasks()
        for task in tasks:
            self.delete_task(task['id'])
        print("Все задачи очищены")


def quick_test():
    """
    Быстрый тест всех функций API.
    Возвращает True если все тесты пройдены, иначе False.
    """
    print("=" * 60)
    print("БЫСТРЫЙ ТЕСТ API УПРАВЛЕНИЯ ЗАДАЧАМИ")
    print("=" * 60)
    
    client = TodoAPIClient()
    
    # Проверка доступности сервера
    print("\n1. Проверка подключения к серверу...")
    try:
        response = requests.get("http://localhost:8000/tasks", timeout=5)
        if response.status_code == 200:
            print("✓ Сервер доступен")
        else:
            print(f"✗ Сервер недоступен (статус: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Не удалось подключиться к серверу!")
        print("  Убедитесь, что сервер запущен: python server.py")
        return False
    
    # Очистка старых данных
    print("\n2. Очистка старых задач...")
    client.clear_all_tasks()
    
    # Тест 1: Создание задач
    print("\n3. Создание тестовых задач...")
    tasks_data = [
        {"title": "Купить молоко", "priority": "high"},
        {"title": "Позвонить маме", "priority": "normal"},
        {"title": "Почитать книгу", "priority": "low"},
    ]
    
    created_tasks = []
    for task_info in tasks_data:
        task = client.create_task(task_info["title"], task_info["priority"])
        if task:
            created_tasks.append(task)
            print(f"  ✓ Создана: '{task_info['title']}' (ID: {task['id']})")
        else:
            print(f"  ✗ Ошибка при создании: '{task_info['title']}'")
            return False
    
    if len(created_tasks) != 3:
        print(f"  ✗ Создано {len(created_tasks)} из 3 задач")
        return False
    
    # Тест 2: Получение задач
    print("\n4. Получение списка задач...")
    all_tasks = client.get_all_tasks()
    if len(all_tasks) == 3:
        print(f"  ✓ Получено {len(all_tasks)} задач")
    else:
        print(f"  ✗ Ожидалось 3 задачи, получено {len(all_tasks)}")
        return False
    
    # Тест 3: Отметка задачи как выполненной
    print("\n5. Отметка задачи как выполненной...")
    task_id = created_tasks[0]['id']
    if client.mark_task_complete(task_id):
        print(f"  ✓ Задача ID:{task_id} отмечена как выполненная")
    else:
        print(f"  ✗ Ошибка при отметке задачи ID:{task_id}")
        return False
    
    # Проверка обновления статуса
    updated_tasks = client.get_all_tasks()
    completed_task = next((t for t in updated_tasks if t['id'] == task_id), None)
    if completed_task and completed_task['isDone']:
        print(f"  ✓ Статус задачи обновлен в базе")
    else:
        print(f"  ✗ Статус задачи не обновлен")
        return False
    
    # Тест 4: Удаление задачи
    print("\n6. Удаление задачи...")
    task_id = created_tasks[1]['id']
    tasks_before = len(client.get_all_tasks())
    
    if client.delete_task(task_id):
        tasks_after = len(client.get_all_tasks())
        if tasks_after == tasks_before - 1:
            print(f"  ✓ Задача ID:{task_id} удалена")
            print(f"  ✓ Задач до удаления: {tasks_before}, после: {tasks_after}")
        else:
            print(f"  ✗ Задача не удалена из базы")
            return False
    else:
        print(f"  ✗ Ошибка при удалении задачи ID:{task_id}")
        return False
    
    # Финальная проверка
    print("\n7. Финальная проверка...")
    final_tasks = client.get_all_tasks()
    completed_count = sum(1 for t in final_tasks if t['isDone'])
    
    print(f"  Всего задач: {len(final_tasks)}")
    print(f"  Выполненных: {completed_count}")
    
    if len(final_tasks) == 2 and completed_count == 1:
        print("\n" + "=" * 60)
        print("✓ ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("✗ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("=" * 60)
        return False


def interactive_mode():
    """Интерактивный режим для ручного тестирования API."""
    client = TodoAPIClient()
    
    print("\n" + "=" * 60)
    print("ИНТЕРАКТИВНЫЙ РЕЖИМ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    while True:
        print("\n" + "-" * 40)
        print("МЕНЮ:")
        print("1. Создать задачу")
        print("2. Показать все задачи")
        print("3. Отметить задачу как выполненную")
        print("4. Удалить задачу")
        print("5. Очистить все задачи")
        print("6. Запустить быстрый тест")
        print("0. Выход")
        print("-" * 40)
        
        choice = input("\nВыберите действие (0-6): ").strip()
        
        if choice == "1":
            print("\n--- СОЗДАНИЕ ЗАДАЧИ ---")
            title = input("Название задачи: ").strip()
            if not title:
                print("❌ Название не может быть пустым!")
                continue
            
            priority = input("Приоритет (low/normal/high) [normal]: ").strip().lower()
            if not priority:
                priority = "normal"
            
            if priority not in ["low", "normal", "high"]:
                print("❌ Недопустимый приоритет! Используйте: low, normal или high")
                continue
            
            task = client.create_task(title, priority)
            if task:
                print(f"\n✅ Задача успешно создана!")
                print(f"   ID: {task['id']}")
                print(f"   Название: {task['title']}")
                print(f"   Приоритет: {task['priority']}")
                print(f"   Статус: {'Выполнена' if task['isDone'] else 'Не выполнена'}")
            else:
                print("❌ Ошибка при создании задачи")
        
        elif choice == "2":
            print("\n--- СПИСОК ВСЕХ ЗАДАЧ ---")
            tasks = client.get_all_tasks()
            
            if not tasks:
                print("📭 Список задач пуст")
            else:
                print(f"📋 Найдено задач: {len(tasks)}\n")
                for i, task in enumerate(tasks, 1):
                    status = "✅" if task['isDone'] else "⭕"
                    print(f"{i}. {status} ID:{task['id']} - {task['title']}")
                    print(f"   Приоритет: {task['priority']}")
                    print(f"   Статус: {'Выполнена' if task['isDone'] else 'Не выполнена'}")
                    if i < len(tasks):
                        print("   " + "-" * 30)
        
        elif choice == "3":
            print("\n--- ОТМЕТКА ЗАДАЧИ КАК ВЫПОЛНЕННОЙ ---")
            try:
                task_id = int(input("Введите ID задачи: "))
                if client.mark_task_complete(task_id):
                    print(f"✅ Задача {task_id} отмечена как выполненная")
                else:
                    print(f"❌ Ошибка: задача {task_id} не найдена")
            except ValueError:
                print("❌ Ошибка: ID должен быть числом")
        
        elif choice == "4":
            print("\n--- УДАЛЕНИЕ ЗАДАЧИ ---")
            try:
                task_id = int(input("Введите ID задачи для удаления: "))
                if client.delete_task(task_id):
                    print(f"✅ Задача {task_id} удалена")
                else:
                    print(f"❌ Ошибка: задача {task_id} не найдена")
            except ValueError:
                print("❌ Ошибка: ID должен быть числом")
        
        elif choice == "5":
            print("\n--- ОЧИСТКА ВСЕХ ЗАДАЧ ---")
            confirm = input("Вы уверены? Все задачи будут удалены! (y/n): ")
            if confirm.lower() == 'y':
                client.clear_all_tasks()
                print("✅ Все задачи удалены")
            else:
                print("❌ Операция отменена")
        
        elif choice == "6":
            print("\n--- ЗАПУСК БЫСТРОГО ТЕСТА ---")
            success = quick_test()
            if success:
                print("✅ Быстрый тест завершен успешно!")
            else:
                print("❌ Быстрый тест завершен с ошибками")
        
        elif choice == "0":
            print("\n👋 Выход из программы")
            break
        
        else:
            print("❌ Неверный выбор. Введите число от 0 до 6")


def check_server_status():
    """Проверяет доступность сервера."""
    try:
        response = requests.get("http://localhost:8000/tasks", timeout=3)
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТЕР API УПРАВЛЕНИЯ ЗАДАЧАМИ")
    print("=" * 60)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        # Если аргументов нет, показываем меню выбора
        print("\nВыберите режим работы:")
        print("  1. Быстрый тест (quick)")
        print("  2. Интерактивный режим (interactive)")
        print("\nВведите номер или название режима: ", end="")
        user_input = input().strip().lower()
        
        if user_input in ["1", "quick", "q"]:
            mode = "quick"
        elif user_input in ["2", "interactive", "i", "интерактивный"]:
            mode = "interactive"
        else:
            print("❌ Неверный ввод. Запускаю интерактивный режим по умолчанию.")
            mode = "interactive"
    
    # Проверка сервера перед запуском
    print("\n🔍 Проверка доступности сервера...")
    if not check_server_status():
        print("❌ Сервер недоступен!")
        print("\nЧто делать:")
        print("  1. Убедитесь, что серверный скрипт запущен")
        print("  2. Запустите сервер в отдельном окне командой:")
        print("     python server.py")
        print("  3. Убедитесь, что сервер работает на порту 8000")
        print("\nХотите продолжить без проверки сервера? (y/n): ", end="")
        if input().strip().lower() != 'y':
            print("Выход...")
            sys.exit(1)
    
    # Запуск выбранного режима
    if mode == "quick":
        success = quick_test()
        sys.exit(0 if success else 1)
    else:
        interactive_mode()


# ==============================================================================
# ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ
# ==============================================================================

"""
КОМАНДЫ ДЛЯ ЗАПУСКА:

1. ЗАПУСК СЕРВЕРА (в отдельном окне терминала):
   python server.py
   
   Сервер запустится на http://localhost:8000

2. ЗАПУСК ТЕСТОВ (в другом окне терминала):
   
   Вариант 1 - Быстрый тест (автоматическая проверка всех функций):
   python test_tasks.py quick
   
   Вариант 2 - Интерактивный режим (ручное тестирование с меню):
   python test_tasks.py interactive
   
   Вариант 3 - Без аргументов (предложит выбрать режим):
   python test_tasks.py

ЧТО ТЕСТИРУЕТСЯ:

1. Быстрый тест проверяет:
   - Доступность сервера
   - Создание задач с разными приоритетами
   - Получение списка задач
   - Отметку задачи как выполненной
   - Удаление задачи
   - Сохранение состояния между операциями

2. Интерактивный режим позволяет:
   - Создавать задачи с любыми параметрами
   - Просматривать все задачи
   - Отмечать задачи как выполненные
   - Удалять отдельные задачи
   - Очищать весь список задач
   - Запускать быстрый тест из меню

ТРЕБОВАНИЯ:

1. Установленный Python 3.6+
2. Установленная библиотека requests:
   pip install requests
3. Запущенный сервер (server.py) на порту 8000

СТРУКТУРА API (для справки):

GET    /tasks              - получить все задачи
POST   /tasks              - создать задачу
POST   /tasks/{id}/complete - отметить задачу как выполненную
DELETE /tasks/{id}         - удалить задачу

Примеры ручного тестирования через curl (если нужно):

# Создание задачи:
curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d "{\"title\": \"Тест\", \"priority\": \"high\"}"

# Получение задач:
curl http://localhost:8000/tasks

# Отметка как выполненной:
curl -X POST http://localhost:8000/tasks/1/complete

# Удаление:
curl -X DELETE http://localhost:8000/tasks/1
"""
