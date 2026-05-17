import { useSearchParams } from 'react-router-dom'
import { FilterType } from '../types/task'

const FILTERS: FilterType[] = ['all', 'active', 'completed']

export function FilterTabs() {
  const [searchParams, setSearchParams] = useSearchParams()
  const current = (searchParams.get('filter') as FilterType) ?? 'all'

  return (
    <div className="flex gap-1 mb-4">
      {FILTERS.map((f) => (
        <button
          key={f}
          onClick={() => setSearchParams(f === 'all' ? {} : { filter: f })}
          className={`px-3 py-1 text-sm rounded capitalize ${
            current === f ? 'bg-blue-500 text-white' : 'bg-gray-100 hover:bg-gray-200'
          }`}
        >
          {f}
        </button>
      ))}
    </div>
  )
}
