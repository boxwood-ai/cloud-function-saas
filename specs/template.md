# Service Name: My API Service
Description: What your service does in one line
Runtime: Node.js 20

## Endpoints

### GET /items
- Description: List all items
- Output: { items: array }

### POST /items
- Description: Create new item
- Input: { name: string, value: number }
- Output: { item: Item, id: string }

### GET /items/:id
- Description: Get specific item
- Output: Item object

## Models

### Item
- id: string (auto-generated)
- name: string (required)
- value: number
- createdAt: timestamp