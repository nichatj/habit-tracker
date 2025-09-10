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
        <li class="p-4 bg-white rounded-xl shadow flex items-center justify-between">
          <div>
            <div class="font-semibold text-lg">{h.name}</div>
            <div class="text-sm text-gray-600">Streak: {h.streak} day{s(h.streak)}</div>
          </div>
          <div class="flex gap-2">
            <button
              class="px-3 py-1 rounded-md bg-emerald-600 text-white hover:bg-emerald-700"
              on:click={() => toggle(h.id)}
            >Complete</button>
            <button
              class="px-3 py-1 rounded-md bg-gray-200 hover:bg-gray-300"
              on:click={() => remove(h.id)}
            >Delete</button>
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</div>
