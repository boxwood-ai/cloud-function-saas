# Service Name: Todo List API
Description: Simple task management service
Runtime: Node.js 20

## Endpoints

### GET /todos
- Description: Get all todos
- Output: { todos: array }

### POST /todos
- Description: Create new todo
- Input: { title: string, completed: boolean }
- Output: { todo: Todo, id: string }

### PUT /todos/:id
- Description: Update todo status
- Input: { completed: boolean }
- Output: { todo: Todo }

### DELETE /todos/:id
- Description: Delete a todo
- Output: { success: boolean }

## Models

### Todo
- id: string (auto-generated)
- title: string (required)
- completed: boolean (default: false)
- createdAt: timestamp