"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Filter, type Task } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { TaskForm } from "@/components/TaskForm";
import { TaskItem } from "@/components/TaskItem";

const FILTERS: Filter[] = ["all", "active", "completed"];

export default function TasksPage() {
  const router = useRouter();
  const { token, ready, signOut } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (ready && !token) router.replace("/sign-in");
  }, [ready, token, router]);

  const refresh = useCallback(
    async (t: string, f: Filter) => {
      setError(null);
      try {
        const data = await api.listTasks(t, f);
        setTasks(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (token) refresh(token, filter);
  }, [token, filter, refresh]);

  if (!ready || !token) return null;

  const onAdd = async (title: string) => {
    const created = await api.createTask(token, title);
    if (filter === "completed") return;
    setTasks((prev) => [created, ...prev]);
  };

  const onToggle = async (task: Task) => {
    const updated = await api.updateTask(token, task.id, { completed: !task.completed });
    setTasks((prev) =>
      filter === "all"
        ? prev.map((t) => (t.id === updated.id ? updated : t))
        : prev.filter((t) => t.id !== updated.id),
    );
  };

  const onDelete = async (task: Task) => {
    await api.deleteTask(token, task.id);
    setTasks((prev) => prev.filter((t) => t.id !== task.id));
  };

  return (
    <div className="container">
      <div className="header">
        <h1>Todo</h1>
        <button className="btn secondary" onClick={signOut}>Sign out</button>
      </div>

      <div className="card">
        <TaskForm onAdd={onAdd} />
        <div className="filters" style={{ marginTop: "1rem" }}>
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`filter ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
        {loading ? (
          <p>Loading…</p>
        ) : tasks.length === 0 ? (
          <p style={{ color: "#888" }}>No tasks.</p>
        ) : (
          <ul className="task-list">
            {tasks.map((t) => (
              <TaskItem key={t.id} task={t} onToggle={onToggle} onDelete={onDelete} />
            ))}
          </ul>
        )}
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  );
}
