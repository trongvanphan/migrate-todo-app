import { useState, useRef, useEffect } from 'react'
import { Task } from '../types/task'
import { toggleTask, updateTaskTitle, deleteTask } from '../lib/firestore'

interface Props {
  task: Task
  uid: string
}

export function TaskItem({ task, uid }: Props) {
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(task.title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  const saveEdit = async () => {
    const trimmed = editTitle.trim()
    if (trimmed && trimmed !== task.title) {
      await updateTaskTitle(uid, task.id, trimmed)
    }
    setEditing(false)
    setEditTitle(task.title)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') saveEdit()
    if (e.key === 'Escape') {
      setEditTitle(task.title)
      setEditing(false)
    }
  }

  return (
    <li className="flex items-center gap-3 py-2 border-b last:border-b-0">
      <input
        type="checkbox"
        checked={task.completed}
        onChange={(e) => toggleTask(uid, task.id, e.target.checked)}
        className="w-4 h-4 cursor-pointer"
      />
      {editing ? (
        <input
          ref={inputRef}
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={saveEdit}
          onKeyDown={handleKeyDown}
          className="flex-1 px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      ) : (
        <span
          onDoubleClick={() => {
            setEditing(true)
            setEditTitle(task.title)
          }}
          className={`flex-1 cursor-pointer ${task.completed ? 'line-through text-gray-400' : ''}`}
        >
          {task.title}
        </span>
      )}
      <button
        onClick={() => deleteTask(uid, task.id)}
        className="text-gray-400 hover:text-red-500 text-sm px-2"
        aria-label="Delete task"
      >
        ✕
      </button>
    </li>
  )
}
