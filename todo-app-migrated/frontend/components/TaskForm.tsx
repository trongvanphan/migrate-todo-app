"use client";

import { FormEvent, useState } from "react";

export function TaskForm({ onAdd }: { onAdd: (title: string) => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const t = title.trim();
    if (!t) return;
    setBusy(true);
    try {
      await onAdd(t);
      setTitle("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="row" onSubmit={onSubmit}>
      <input
        className="input"
        placeholder="What needs to be done?"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        autoFocus
      />
      <button className="btn" type="submit" disabled={busy || !title.trim()}>
        Add
      </button>
    </form>
  );
}
