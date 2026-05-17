import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useFilteredTasks } from '../hooks/useFilteredTasks'
import { Task } from '../types/task'

const tasks: Task[] = [
  { id: '1', title: 'Active task', completed: false, createdAt: null },
  { id: '2', title: 'Done task', completed: true, createdAt: null },
]

describe('useFilteredTasks', () => {
  it('returns all tasks for "all" filter', () => {
    const { result } = renderHook(() => useFilteredTasks(tasks, 'all'))
    expect(result.current).toHaveLength(2)
  })

  it('returns only active tasks for "active" filter', () => {
    const { result } = renderHook(() => useFilteredTasks(tasks, 'active'))
    expect(result.current).toHaveLength(1)
    expect(result.current[0].id).toBe('1')
  })

  it('returns only completed tasks for "completed" filter', () => {
    const { result } = renderHook(() => useFilteredTasks(tasks, 'completed'))
    expect(result.current).toHaveLength(1)
    expect(result.current[0].id).toBe('2')
  })
})
