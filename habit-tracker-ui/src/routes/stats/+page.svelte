<script lang="ts">
  import { onMount } from "svelte";
  import BarChart from "$lib/components/BarChart.svelte";

  type Stats = {
    total_habits: number;
    total_completions: number;
    longest_streak: number;
    average_streak: number;
  };

  type Habit = { id:number; name:string; streak:number };

  let stats: Stats | null = null;
  let labels: string[] = [];
  let values: number[] = [];
  let loading = true;
  let error = "";

  async function load() {
    try {
      const [sres, hres] = await Promise.all([
        fetch("/api/stats"),
        fetch("/api/habits")
      ]);
      if (!sres.ok) throw new Error(await sres.text());
      if (!hres.ok) throw new Error(await hres.text());

      stats = await sres.json();
      const data: { habits: Habit[] } = await hres.json();

      // sort by streak desc for a nicer chart
      const sorted = [...data.habits].sort((a, b) => (b.streak ?? 0) - (a.streak ?? 0));
      labels = sorted.map(h => h.name);
      values = sorted.map(h => h.streak ?? 0);
    } catch (e) {
      error = (e as Error).message;
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<div class="max-w-4xl mx-auto p-6 space-y-6">
  <h1 class="text-3xl font-bold">Stats</h1>

  {#if loading}
    <p>Loading…</p>
  {:else if error}
    <p class="text-red-600">Error: {error}</p>
  {:else if stats}
    <!-- KPI cards -->
    <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="p-4 rounded-xl bg-white shadow border">
        <div class="text-sm text-gray-500">Total Habits</div>
        <div class="text-2xl font-semibold mt-1">{stats.total_habits}</div>
      </div>
      <div class="p-4 rounded-xl bg-white shadow border">
        <div class="text-sm text-gray-500">Total Completions</div>
        <div class="text-2xl font-semibold mt-1">{stats.total_completions}</div>
      </div>
      <div class="p-4 rounded-xl bg-white shadow border">
        <div class="text-sm text-gray-500">Longest Streak</div>
        <div class="text-2xl font-semibold mt-1">{stats.longest_streak}</div>
      </div>
      <div class="p-4 rounded-xl bg-white shadow border">
        <div class="text-sm text-gray-500">Average Streak</div>
        <div class="text-2xl font-semibold mt-1">{stats.average_streak}</div>
      </div>
    </div>

    <!-- Bar chart -->
    <div class="p-4 rounded-xl bg-white shadow border">
      <div class="mb-3 font-medium">Streaks by Habit</div>
      <BarChart {labels} {values} />
    </div>
  {/if}
</div>
