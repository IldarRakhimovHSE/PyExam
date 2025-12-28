import http.server
import json
import os
import urllib.parse
from http import HTTPStatus
from typing import Optional, Dict, Any, List


class TaskManager:
    """Класс для управления задачами: создание, чтение, обновление, удаление."""
    
    def __init__(self, filename: str = 'tasks.txt') -> None:
        """
        Инициализация менеджера задач.
        
        Args:
            filename: Имя файла для сохранения задач
        """
        self.filename = filename
        self.tasks: List[Dict[str, Any]] = []
        self.load_tasks()
    
    def load_tasks(self) -> None:
        """Загружает задачи из файла, если он существует."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.tasks = json.loads(content)
            except (json.JSONDecodeError, IOError):
                self.tasks = []
    
    def save_tasks(self) -> None:
        """Сохраняет все задачи в файл."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except IOError:
            # В реальном приложении здесь лучше логировать ошибку
            pass
    
    def get_next_id(self) -> int:
        """Возвращает следующий доступный ID для задачи."""
        if not self.tasks:
            return 1
        return max(task['id'] for task in self.tasks) + 1
    
    def create_task(self, title: str, priority: str = 'normal') -> Dict[str, Any]:
        """
        Создает новую задачу.
        
        Args:
            title: Название задачи
            priority: Приоритет задачи (low, normal, high)
            
        Returns:
            Созданная задача
        """
        task = {
            'id': self.get_next_id(),
            'title': title,
            'priority': priority,
            'isDone': False
        }
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Возвращает список всех задач."""
        return self.tasks
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Находит задачу по ID.
        
        Args:
            task_id: ID задачи
            
        Returns:
            Задача или None, если не найдена
        """
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None
    
    def mark_as_done(self, task_id: int) -> bool:
        """
        Отмечает задачу как выполненную.
        
        Args:
            task_id: ID задачи
            
        Returns:
            True если задача найдена и обновлена, иначе False
        """
        task = self.get_task_by_id(task_id)
        if task:
            task['isDone'] = True
            self.save_tasks()
            return True
        return False
    
    def delete_task(self, task_id: int) -> bool:
        """
        Удаляет задачу.
        
        Args:
            task_id: ID задачи
            
        Returns:
            True если задача найдена и удалена, иначе False
        """
        task = self.get_task_by_id(task_id)
        if task:
            self.tasks.remove(task)
            self.save_tasks()
            return True
        return False


class TodoHandler(http.server.BaseHTTPRequestHandler):
    """HTTP-обработчик для управления задачами."""
    
    def __init__(self, *args, **kwargs) -> None:
        """Инициализация обработчика с менеджером задач."""
        self.task_manager = kwargs.pop('task_manager')
        super().__init__(*args, **kwargs)
    
    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        """
        Отправляет JSON-ответ.
        
        Args:
            data: Данные для отправки
            status: HTTP-статус код
        """
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        if data is not None:
            json_data = json.dumps(data, ensure_ascii=False)
            self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error(self, status: int, message: str) -> None:
        """
        Отправляет ошибку в формате JSON.
        
        Args:
            status: HTTP-статус код
            message: Сообщение об ошибке
        """
        self._send_json({'error': message}, status)
    
    def _parse_json_body(self) -> Optional[Dict[str, Any]]:
        """
        Парсит JSON-тело запроса.
        
        Returns:
            Распарсенные данные или None в случае ошибки
        """
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return None
            
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        except (json.JSONDecodeError, ValueError):
            return None
    
    def _extract_task_id_from_path(self, path: str) -> Optional[int]:
        """
        Извлекает ID задачи из пути.
        
        Args:
            path: Путь запроса
            
        Returns:
            ID задачи или None если не удалось извлечь
        """
        try:
            # Удаляем начальный и конечный слэши и разбиваем путь
            parts = path.strip('/').split('/')
            if len(parts) >= 2 and parts[0] == 'tasks':
                return int(parts[1])
        except (ValueError, IndexError):
            pass
        return None
    
    def _handle_get_tasks(self) -> None:
        """Обрабатывает GET запрос для получения всех задач."""
        tasks = self.task_manager.get_all_tasks()
        self._send_json(tasks)
    
    def _handle_post_tasks(self) -> None:
        """Обрабатывает POST запрос для создания новой задачи."""
        data = self._parse_json_body()
        
        if data is None:
            self._send_error(HTTPStatus.BAD_REQUEST, 'Invalid JSON')
            return
        
        title = data.get('title')
        priority = data.get('priority', 'normal')
        
        # Валидация данных
        if not title:
            self._send_error(HTTPStatus.BAD_REQUEST, 'title is required')
            return
        
        if priority not in ['low', 'normal', 'high']:
            self._send_error(HTTPStatus.BAD_REQUEST, 
                           'priority must be low, normal, or high')
            return
        
        # Создание задачи
        task = self.task_manager.create_task(title, priority)
        self._send_json(task, HTTPStatus.CREATED)
    
    def _handle_post_tasks_complete(self) -> None:
        """Обрабатывает POST запрос для отметки задачи как выполненной."""
        task_id = self._extract_task_id_from_path(self.path)
        
        if task_id is None:
            self._send_error(HTTPStatus.BAD_REQUEST, 'Invalid task ID')
            return
        
        if self.task_manager.mark_as_done(task_id):
            self._send_json({}, HTTPStatus.OK)
        else:
            self._send_error(HTTPStatus.NOT_FOUND, 'Task not found')
    
    def _handle_delete_task(self) -> None:
        """Обрабатывает DELETE запрос для удаления задачи."""
        task_id = self._extract_task_id_from_path(self.path)
        
        if task_id is None:
            self._send_error(HTTPStatus.BAD_REQUEST, 'Invalid task ID')
            return
        
        if self.task_manager.delete_task(task_id):
            self._send_json({}, HTTPStatus.OK)
        else:
            self._send_error(HTTPStatus.NOT_FOUND, 'Task not found')
    
    def do_GET(self) -> None:
        """
        Обрабатывает GET запросы.
        
        Поддерживаемые пути:
        - GET /tasks - получить все задачи
        """
        if self.path == '/tasks':
            self._handle_get_tasks()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, 'Route not found')
    
    def do_POST(self) -> None:
        """
        Обрабатывает POST запросы.
        
        Поддерживаемые пути:
        - POST /tasks - создать новую задачу
        - POST /tasks/{id}/complete - отметить задачу как выполненную
        """
        if self.path == '/tasks':
            self._handle_post_tasks()
        elif self.path.startswith('/tasks/') and self.path.endswith('/complete'):
            self._handle_post_tasks_complete()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, 'Route not found')
    
    def do_DELETE(self) -> None:
        """
        Обрабатывает DELETE запросы.
        
        Поддерживаемые пути:
        - DELETE /tasks/{id} - удалить задачу
        """
        if self.path.startswith('/tasks/'):
            self._handle_delete_task()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, 'Route not found')
    
    def log_message(self, format: str, *args) -> None:
        """Переопределяет логирование для более чистого вывода."""
        # Можно раскомментировать для отладки
        # print(f"{self.address_string()} - {format % args}")
        pass


def run_server(port: int = 8000) -> None:
    """
    Запускает HTTP-сервер.
    
    Args:
        port: Порт для запуска сервера
    """
    task_manager = TaskManager()
    
    # Создаем обработчик с передачей менеджера задач
    handler_class = lambda *args, **kwargs: TodoHandler(
        *args, task_manager=task_manager, **kwargs
    )
    
    server = http.server.HTTPServer(('', port), handler_class)
    print(f'Сервер запущен на порту {port}')
    print('Доступные эндпоинты:')
    print('  GET    /tasks                    - получить все задачи')
    print('  POST   /tasks                    - создать задачу')
    print('  POST   /tasks/<id>/complete      - отметить задачу как выполненную')
    print('  DELETE /tasks/<id>               - удалить задачу')
    print('\nДля остановки сервера нажмите Ctrl+C')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nСервер остановлен')


if __name__ == '__main__':
    run_server(8000)
