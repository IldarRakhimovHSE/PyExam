import http.server
import json
import os
import urllib.parse
from http import HTTPStatus

class TaskManager:
    def __init__(self, filename='tasks.txt'):
        self.filename = filename
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.tasks = json.loads(content)
            except:
                self.tasks = []

    def save_tasks(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except:
            pass

    def create_task(self, title, priority):
        new_id = 1 if not self.tasks else self.tasks[-1]['id'] + 1
        task = {
            'id': new_id,
            'title': title,
            'priority': priority,
            'isDone': False
        }
        self.tasks.append(task)
        self.save_tasks()
        return task

    def get_all_tasks(self):
        return self.tasks

    def mark_as_done(self, task_id):
        for task in self.tasks:
            if task['id'] == task_id:
                task['isDone'] = True
                self.save_tasks()
                return True
        return False

    def delete_task(self, task_id):
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                del self.tasks[i]
                self.save_tasks()
                return True
        return False

class TodoHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.task_manager = kwargs.pop('task_manager')
        super().__init__(*args, **kwargs)

    def _send_json(self, data, status=HTTPStatus.OK):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        if self.path == '/tasks':
            tasks = self.task_manager.get_all_tasks()
            self._send_json(tasks)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Route not found')

    def do_POST(self):
        if self.path == '/tasks':
            try:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
                
                title = data.get('title')
                priority = data.get('priority', 'normal')
                
                if not title:
                    self._send_json({'error': 'title is required'}, HTTPStatus.BAD_REQUEST)
                    return
                
                if priority not in ['low', 'normal', 'high']:
                    self._send_json({'error': 'priority must be low, normal, or high'}, 
                                   HTTPStatus.BAD_REQUEST)
                    return
                
                task = self.task_manager.create_task(title, priority)
                self._send_json(task, HTTPStatus.CREATED)
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, HTTPStatus.BAD_REQUEST)
            except Exception:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        elif self.path.startswith('/tasks/') and self.path.endswith('/complete'):
            try:
                task_id = int(self.path.split('/')[-2])
                if self.task_manager.mark_as_done(task_id):
                    self._send_json({}, HTTPStatus.OK)
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, 'Task not found')
            except (ValueError, IndexError):
                self.send_error(HTTPStatus.BAD_REQUEST, 'Invalid task ID')
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Route not found')

    def do_DELETE(self):
        if self.path.startswith('/tasks/'):
            try:
                task_id = int(self.path.split('/')[-1])
                if self.task_manager.delete_task(task_id):
                    self._send_json({}, HTTPStatus.OK)
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, 'Task not found')
            except (ValueError, IndexError):
                self.send_error(HTTPStatus.BAD_REQUEST, 'Invalid task ID')
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Route not found')

def run_server(port=8000):
    task_manager = TaskManager()
    handler = lambda *args, **kwargs: TodoHandler(*args, task_manager=task_manager, **kwargs)
    server = http.server.HTTPServer(('', port), handler)
    print(f'Server running on port {port}')
    server.serve_forever()

run_server(8000)

#Каждое дело характеризуется: title, priority, isDone, id
#При создании нового дела isDone автоматически False, а id - 1, если первое дело, либо предыдущий id + 1, priority по умолчанию normal, но можно задать low или high
#Создание задачи - curl -X POST http://127.0.0.1:8000/tasks ^
                        -H "Content-Type: application/json" ^
                        -d "{\"title\": \"Купить молоко\", \"priority\": \"high\"}"
                   или
                   curl -X POST http://localhost:8000/tasks ^
                        -H "Content-Type: application/json" ^
                        -d "{\"title\": \"Купить молоко\", \"priority\": \"high\"}"
#Получение списка всех задач - curl http://127.0.0.1:8000/tasks или http://localhost:8000/tasks
#Изменение статуса задачи (по id) - curl -X POST http://127.0.0.1:8000/tasks/нужный_id/complete или curl -X POST http://localhost:8000/tasks/нужный_id/complete
#Также добавлена API удаления задачи (по id) - curl -X DELETE http://127.0.0.1:8000/tasks/нужный_id или curl -X DELETE http://localhost:8000/tasks/нужный_id
