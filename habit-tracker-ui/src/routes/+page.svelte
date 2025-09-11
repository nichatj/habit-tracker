<script lang="ts">
  import { onMount } from "svelte";

  type Habit = {
    id: number;
    name: string;
    streak: number;
    created: string;
    last_completed: string | null;
    history?: string[];
  };

  let habits: Habit[] = [];
  let name = "";
  let loading = false;
  let errorMsg = "";
  let editingId: number | null = null;
  let editName = "";
  let editCreated = "";
  let editHistory = ""; // newline or comma-separated YYYY-MM-DD

  // tiny helper for pluralization
  function s(n: number) { return n === 1 ? "" : "s"; }

  async function load() {
    try {
      loading = true;
      const res = await fetch("/api/habits");
      if (!res.ok) throw new Error(await res.text());
      const data: { habits: Habit[] } = await res.json();
      habits = data.habits;
    } catch (e) {
      errorMsg = (e as Error).message;
    } finally {
      loading = false;
    }
  }

  async function addHabit() {
    const trimmed = name.trim();
    if (!trimmed) return;
    const res = await fetch("/api/habits", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: trimmed })
    });
    if (!res.ok) { errorMsg = await res.text(); return; }
    name = "";
    await load();
  }

  async function toggle(habitId: number) {
    const res = await fetch(`/api/habits/${habitId}/toggle`, { method: "POST" });
    if (!res.ok) { errorMsg = await res.text(); return; }
    await load();
  }

  async function remove(habitId: number) {
    const res = await fetch(`/api/habits/${habitId}`, { method: "DELETE" });
    if (!res.ok) { errorMsg = await res.text(); return; }
    await load();
  }
  function startEdit(h: Habit) {
  editingId = h.id;
  editName = h.name;
  editCreated = h.created; // already "YYYY-MM-DD"
  editHistory = (h.history ?? []).join("\n");
}

function cancelEdit() {
  editingId = null;
  editName = "";
  editCreated = "";
  editHistory = "";
}

async function saveEdit(habitId: number) {
  const payload: any = {};
  if (editName.trim()) payload.name = editName.trim();
  if (editCreated) payload.created = editCreated;

  // turn textarea into array of dates
  const dates = Array.from(
    new Set(
      editHistory
        .replace(/,/g, "\n")
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean)
    )
  );
  payload.history = dates; // replace whole history

  const res = await fetch(`/api/habits/${habitId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) { errorMsg = await res.text(); return; }
  editingId = null;
  await load();
}
  onMount(load);
</script>


<div class="max-w-3xl mx-auto p-6 space-y-6">
  <h1 class="text-3xl font-bold">My Habits</h1>

  <form class="flex gap-3" on:submit|preventDefault={addHabit}>
    <input
      class="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200"
      placeholder="New habit…"
      bind:value={name}
    />
    <button class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700">
      Add
    </button>
  </form>

  {#if errorMsg}
    <p class="text-red-600">Error: {errorMsg}</p>
  {/if}

  {#if loading}
    <p>Loading…</p>
  {:else if habits.length === 0}
    <p class="text-gray-500">No habits yet. Add your first!</p>
  {:else}
    <ul class="grid gap-4">
      {#each habits as h (h.id)}
        <li class="p-4 bg-white rounded-xl shadow flex items-start justify-between gap-4">
  <div class="min-w-0 flex-1">
    {#if editingId === h.id}
      <div class="grid sm:grid-cols-2 gap-3">
        <label class="text-sm">
          <div class="text-gray-600 mb-1">Name</div>
          <input class="w-full border rounded-lg px-3 py-2" bind:value={editName} />
        </label>
        <label class="text-sm">
          <div class="text-gray-600 mb-1">Created</div>
          <input class="w-full border rounded-lg px-3 py-2" type="date" bind:value={editCreated} />
        </label>
        <label class="text-sm sm:col-span-2">
          <div class="text-gray-600 mb-1">Completions (YYYY-MM-DD, one per line)</div>
          <textarea class="w-full border rounded-lg px-3 py-2 h-28" bind:value={editHistory}></textarea>
        </label>
      </div>
    {:else}
      <div class="font-semibold text-lg truncate">{h.name}</div>
      <div class="text-sm text-gray-600">Streak: {h.streak} day{s(h.streak)}</div>
      <div class="text-xs text-gray-500 mt-1">Created: {h.created}</div>
    {/if}
  </div>

  <div class="flex gap-2">
    {#if editingId === h.id}
      <button class="px-3 py-1 rounded-md bg-blue-600 text-white hover:bg-blue-700" on:click={() => saveEdit(h.id)}>Save</button>
      <button class="px-3 py-1 rounded-md bg-gray-200 hover:bg-gray-300" on:click={cancelEdit}>Cancel</button>
    {:else}
      <button class="px-3 py-1 rounded-md bg-emerald-600 text-white hover:bg-emerald-700" on:click={() => toggle(h.id)}>Complete</button>
      <button class="px-3 py-1 rounded-md bg-gray-200 hover:bg-gray-300" on:click={() => startEdit(h)}>Edit</button>
      <button class="px-3 py-1 rounded-md bg-gray-200 hover:bg-gray-300" on:click={() => remove(h.id)}>Delete</button>
    {/if}
  </div>
</li>

      {/each}
    </ul>
  {/if}
</div>
