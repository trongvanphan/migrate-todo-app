import { Timestamp } from 'firebase/firestore'

export interface Task {
  id: string
  title: string
  completed: boolean
  createdAt: Timestamp | null
}

export type FilterType = 'all' | 'active' | 'completed'
