import { useSearchParams } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { AuthPanel } from './components/AuthPanel'
import { TaskForm } from './components/TaskForm'
import { TaskList } from './components/TaskList'
import { FilterTabs } from './components/FilterTabs'
import { useTasks } from './hooks/useTasks'
import { useFilteredTasks } from './hooks/useFilteredTasks'
import { FilterType } from './types/task'

function TodoApp() {
  const { user, loading } = useAuth()
  const [searchParams] = useSearchParams()
  const filter = (searchParams.get('filter') as FilterType) ?? 'all'

  const uid = user?.uid ?? null
  const { tasks, loading: tasksLoading } = useTasks(uid)
  const filteredTasks = useFilteredTasks(tasks, filter)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="text-gray-400">Loading…</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-2xl mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-800">Todo</h1>
          <AuthPanel />
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-4 py-6">
        {uid && <TaskForm uid={uid} />}
        <FilterTabs />
        {tasksLoading ? (
          <p className="text-gray-400 text-sm text-center py-4">Loading tasks…</p>
        ) : (
          <TaskList tasks={filteredTasks} uid={uid ?? ''} />
        )}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <TodoApp />
    </AuthProvider>
  )
}
