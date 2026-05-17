import {
  collection,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
  serverTimestamp,
  query,
  orderBy,
  onSnapshot,
  Unsubscribe,
} from 'firebase/firestore'
import { db } from '../firebase'
import { Task } from '../types/task'

const tasksRef = (uid: string) => collection(db, 'tasks', uid, 'items')

export function subscribeTasks(uid: string, cb: (tasks: Task[]) => void): Unsubscribe {
  const q = query(tasksRef(uid), orderBy('createdAt', 'asc'))
  return onSnapshot(q, (snap) => {
    const tasks: Task[] = snap.docs.map((d) => ({
      id: d.id,
      ...(d.data() as Omit<Task, 'id'>),
    }))
    cb(tasks)
  })
}

export async function addTask(uid: string, title: string): Promise<void> {
  const trimmed = title.trim()
  if (!trimmed) return
  await addDoc(tasksRef(uid), {
    title: trimmed,
    completed: false,
    createdAt: serverTimestamp(),
  })
}

export async function toggleTask(
  uid: string,
  taskId: string,
  completed: boolean
): Promise<void> {
  await updateDoc(doc(db, 'tasks', uid, 'items', taskId), { completed })
}

export async function updateTaskTitle(
  uid: string,
  taskId: string,
  title: string
): Promise<void> {
  const trimmed = title.trim()
  if (!trimmed) return
  await updateDoc(doc(db, 'tasks', uid, 'items', taskId), { title: trimmed })
}

export async function deleteTask(uid: string, taskId: string): Promise<void> {
  await deleteDoc(doc(db, 'tasks', uid, 'items', taskId))
}
