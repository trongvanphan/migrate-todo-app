import { Task } from '../types/task'
import { TaskItem } from './TaskItem'

interface Props {
  tasks: Task[]
  uid: string
}

export function TaskList({ tasks, uid }: Props) {
  if (tasks.length === 0) {
    return <p className="text-gray-400 text-sm py-4 text-center">No tasks yet.</p>
  }
  return (
    <ul className="divide-y">
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} uid={uid} />
      ))}
    </ul>
  )
}
