import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import { TaskItem } from '../components/TaskItem'
import { Task } from '../types/task'
import * as firestoreLib from '../lib/firestore'

vi.mock('../lib/firestore', () => ({
  toggleTask: vi.fn(),
  updateTaskTitle: vi.fn(),
  deleteTask: vi.fn(),
  subscribeTasks: vi.fn(),
  addTask: vi.fn(),
}))

vi.mock('../firebase', () => ({
  db: {},
  auth: {},
  app: {},
}))

vi.mock('firebase/firestore', () => ({
  getFirestore: vi.fn(),
  collection: vi.fn(),
  addDoc: vi.fn(),
  updateDoc: vi.fn(),
  deleteDoc: vi.fn(),
  doc: vi.fn(),
  serverTimestamp: vi.fn(),
  query: vi.fn(),
  orderBy: vi.fn(),
  onSnapshot: vi.fn(),
  Timestamp: { now: () => ({ seconds: 0, nanoseconds: 0 }) },
}))

const mockTask: Task = {
  id: 'task-1',
  title: 'Buy milk',
  completed: false,
  createdAt: null,
}

describe('TaskItem', () => {
  it('renders task title', () => {
    render(<TaskItem task={mockTask} uid="user-1" />)
    expect(screen.getByText('Buy milk')).toBeInTheDocument()
  })

  it('calls toggleTask when checkbox clicked', async () => {
    render(<TaskItem task={mockTask} uid="user-1" />)
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)
    expect(firestoreLib.toggleTask).toHaveBeenCalledWith('user-1', 'task-1', true)
  })

  it('calls deleteTask when delete button clicked', () => {
    render(<TaskItem task={mockTask} uid="user-1" />)
    fireEvent.click(screen.getByLabelText('Delete task'))
    expect(firestoreLib.deleteTask).toHaveBeenCalledWith('user-1', 'task-1')
  })

  it('enters edit mode on double-click', () => {
    render(<TaskItem task={mockTask} uid="user-1" />)
    fireEvent.dblClick(screen.getByText('Buy milk'))
    expect(screen.getByDisplayValue('Buy milk')).toBeInTheDocument()
  })

  it('does not save on Escape — reverts title', () => {
    render(<TaskItem task={mockTask} uid="user-1" />)
    fireEvent.dblClick(screen.getByText('Buy milk'))
    const input = screen.getByDisplayValue('Buy milk')
    fireEvent.change(input, { target: { value: 'Changed' } })
    fireEvent.keyDown(input, { key: 'Escape' })
    expect(firestoreLib.updateTaskTitle).not.toHaveBeenCalled()
    expect(screen.getByText('Buy milk')).toBeInTheDocument()
  })

  it('does not save empty title on Enter', async () => {
    render(<TaskItem task={mockTask} uid="user-1" />)
    fireEvent.dblClick(screen.getByText('Buy milk'))
    const input = screen.getByDisplayValue('Buy milk')
    fireEvent.change(input, { target: { value: '' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(firestoreLib.updateTaskTitle).not.toHaveBeenCalled()
  })

  it('does not save unchanged title', async () => {
    render(<TaskItem task={mockTask} uid="user-1" />)
    fireEvent.dblClick(screen.getByText('Buy milk'))
    const input = screen.getByDisplayValue('Buy milk')
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(firestoreLib.updateTaskTitle).not.toHaveBeenCalled()
  })

  it('shows strikethrough for completed tasks', () => {
    const completed = { ...mockTask, completed: true }
    render(<TaskItem task={completed} uid="user-1" />)
    const span = screen.getByText('Buy milk')
    expect(span.className).toContain('line-through')
  })
})
