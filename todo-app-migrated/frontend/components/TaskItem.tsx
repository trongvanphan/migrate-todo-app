"use client";

import type { Task } from "@/lib/api";

export function TaskItem({
  task,
  onToggle,
  onDelete,
}: {
  task: Task;
  onToggle: (t: Task) => void;
  onDelete: (t: Task) => void;
}) {
  return (
    <li className="task">
      <input
        type="checkbox"
        checked={task.completed}
        onChange={() => onToggle(task)}
        aria-label={`Toggle ${task.title}`}
      />
      <span className={`title ${task.completed ? "done" : ""}`}>{task.title}</span>
      <button className="btn danger" onClick={() => onDelete(task)} aria-label={`Delete ${task.title}`}>
        Delete
      </button>
    </li>
  );
}
