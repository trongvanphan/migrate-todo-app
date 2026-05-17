import { useEffect, useState } from 'react'
import { Task } from '../types/task'
import { subscribeTasks } from '../lib/firestore'

export function useTasks(uid: string | null) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!uid) {
      setTasks([])
      setLoading(false)
      return
    }
    setLoading(true)
    const unsubscribe = subscribeTasks(uid, (t) => {
      setTasks(t)
      setLoading(false)
    })
    return unsubscribe
  }, [uid])

  return { tasks, loading }
}
