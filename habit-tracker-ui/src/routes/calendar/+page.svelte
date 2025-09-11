<script lang="ts">
  import { onMount } from "svelte";

  // Backend payload: { events: {title, start: 'YYYY-MM-DD', color?: string}[] }
  type ApiEvent = { title: string; start: string; color?: string };

  // local state
  let allEvents: ApiEvent[] = [];
  let eventsByDay: Record<string, ApiEvent[]> = {};

  // calendar state
  const today = new Date();
  let viewYear = today.getFullYear();
  let viewMonth = today.getMonth(); // 0-based
  let selectedKey = toKey(today);

  // fetch events on mount
  onMount(async () => {
    const res = await fetch("/api/calendar");
    if (!res.ok) {
      console.error(await res.text());
      return;
    }
    const data: { events: ApiEvent[] } = await res.json();
    // normalize date keys (strip time if any)
    allEvents = (data.events ?? []).map(e => ({
      ...e,
      start: e.start.slice(0, 10) // YYYY-MM-DD
    }));

    // index by day
    eventsByDay = {};
    for (const ev of allEvents) {
      (eventsByDay[ev.start] ??= []).push(ev);
    }
  });

  // ----- calendar helpers -----
  function toKey(d: Date) {
    const m = d.getMonth() + 1;
    const day = d.getDate();
    return `${d.getFullYear()}-${String(m).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  }

  function startOfMonth(y: number, m: number) {
    return new Date(y, m, 1);
  }
  function endOfMonth(y: number, m: number) {
    return new Date(y, m + 1, 0);
  }
  function addMonths(y: number, m: number, delta: number) {
    const d = new Date(y, m, 1);
    d.setMonth(d.getMonth() + delta);
    return [d.getFullYear(), d.getMonth()] as const;
  }

  // grid for current month (6 rows, Sun → Sat)
  function monthGrid(y: number, m: number) {
    const start = startOfMonth(y, m);
    const end = endOfMonth(y, m);

    const firstWeekday = start.getDay(); // 0=Sun
    const daysInMonth = end.getDate();

    const cells: Date[] = [];
    // days from previous month
    for (let i = 0; i < firstWeekday; i++) {
      const d = new Date(y, m, 1 - (firstWeekday - i));
      cells.push(d);
    }
    // this month
    for (let d = 1; d <= daysInMonth; d++) {
      cells.push(new Date(y, m, d));
    }
    // next month to fill 6 rows (42 cells)
    while (cells.length % 7 !== 0 || cells.length < 42) {
      const last = cells[cells.length - 1];
      const next = new Date(last);
      next.setDate(next.getDate() + 1);
      cells.push(next);
    }
    return cells;
  }

  $: cells = monthGrid(viewYear, viewMonth);
  $: monthName = new Date(viewYear, viewMonth, 1).toLocaleString(undefined, { month: "long", year: "numeric" });

  function prevMonth() {
    [viewYear, viewMonth] = addMonths(viewYear, viewMonth, -1);
  }
  function nextMonth() {
    [viewYear, viewMonth] = addMonths(viewYear, viewMonth, 1);
  }

  // legend from events (habit → color)
  $: legend = (() => {
    const map = new Map<string, string>();
    for (const e of allEvents) if (!map.has(e.title) && e.color) map.set(e.title, e.color);
    return Array.from(map.entries()); // [title,color][]
  })();

  function isSameMonth(d: Date) { return d.getMonth() === viewMonth; }
  function isToday(d: Date) {
    return d.getFullYear() === today.getFullYear() &&
           d.getMonth() === today.getMonth() &&
           d.getDate() === today.getDate();
  }
</script>

<div class="max-w-5xl mx-auto p-6 space-y-6">
  <div class="flex items-center justify-between">
    <h1 class="text-3xl font-bold">Calendar</h1>
    <div class="flex gap-2">
      <button class="px-3 py-1 rounded-lg border hover:bg-gray-50" on:click={prevMonth}>← Prev</button>
      <div class="px-3 py-1 font-medium">{monthName}</div>
      <button class="px-3 py-1 rounded-lg border hover:bg-gray-50" on:click={nextMonth}>Next →</button>
    </div>
  </div>

  <!-- legend -->
  {#if legend.length}
    <div class="flex flex-wrap gap-3 text-sm">
      {#each legend as [name, color]}
        <span class="inline-flex items-center gap-2 px-2 py-1 rounded-full bg-white border shadow-sm">
          <span class="inline-block w-3 h-3 rounded-full" style={`background:${color}`}></span>
          {name}
        </span>
      {/each}
    </div>
  {/if}

  <!-- grid -->
  <div class="rounded-xl overflow-hidden bg-white border shadow">
    <div class="grid grid-cols-7 text-center bg-gray-50 text-sm text-gray-600">
      <div class="py-2">Sun</div><div class="py-2">Mon</div><div class="py-2">Tue</div>
      <div class="py-2">Wed</div><div class="py-2">Thu</div><div class="py-2">Fri</div><div class="py-2">Sat</div>
    </div>

    <div class="grid grid-cols-7">
      {#each cells as d (toKey(d))}
        {#key toKey(d)}
          <button
            class="h-28 p-2 border -mt-px -ml-px text-left relative focus:outline-none focus:ring-2 focus:ring-blue-300
                   {isSameMonth(d) ? 'bg-white' : 'bg-gray-50'}
                   {selectedKey === toKey(d) ? 'ring-2 ring-blue-400 z-10' : ''}"
            on:click={() => (selectedKey = toKey(d))}
            aria-label={`Day ${d.getDate()}`}
          >
            <div class="flex items-center justify-between">
              <span class="text-sm {isSameMonth(d) ? 'text-gray-900' : 'text-gray-400'}">
                {d.getDate()}
              </span>
              {#if isToday(d)}
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-600 text-white">Today</span>
              {/if}
            </div>

            <!-- dots for events -->
            {#if eventsByDay[toKey(d)]?.length}
              <div class="mt-2 flex flex-wrap gap-1">
                {#each eventsByDay[toKey(d)].slice(0, 4) as ev}
                  <span class="w-2.5 h-2.5 rounded-full" style={`background:${ev.color ?? '#0ea5e9'}`}></span>
                {/each}
                {#if eventsByDay[toKey(d)].length > 4}
                  <span class="text-[10px] text-gray-500">+{eventsByDay[toKey(d)].length - 4}</span>
                {/if}
              </div>
            {/if}
          </button>
        {/key}
      {/each}
    </div>
  </div>

  <!-- selected-day details -->
  <div class="rounded-xl bg-white border shadow p-4">
    <div class="text-sm text-gray-600">Selected date</div>
    <div class="text-xl font-semibold">
      {new Date(selectedKey).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
    </div>

    {#if eventsByDay[selectedKey]?.length}
      <ul class="mt-3 space-y-2">
        {#each eventsByDay[selectedKey] as ev}
          <li class="flex items-center gap-3">
            <span class="inline-block w-3 h-3 rounded-full" style={`background:${ev.color ?? '#0ea5e9'}`}></span>
            <span class="font-medium">{ev.title}</span>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="mt-3 text-gray-500">No completions on this day.</p>
    {/if}
  </div>
</div>
