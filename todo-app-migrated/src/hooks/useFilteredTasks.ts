import { useMemo } from 'react'
import { Task, FilterType } from '../types/task'

export function useFilteredTasks(tasks: Task[], filter: FilterType): Task[] {
  return useMemo(() => {
    if (filter === 'active') return tasks.filter((t) => !t.completed)
    if (filter === 'completed') return tasks.filter((t) => t.completed)
    return tasks
  }, [tasks, filter])
}
