<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  /** Bind this from the parent: a set of 'YYYY-MM-DD' strings */
  export let value: Set<string> = new Set();

  /** Which month the calendar shows */
  export let month = new Date(); // any day in the month

  const dispatch = createEventDispatcher<{ input: Set<string> }>();

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Helpers
  const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
  const toISO = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

  function startOfCalendar(d: Date) {
    const first = new Date(d.getFullYear(), d.getMonth(), 1);
    const s = new Date(first);
    s.setDate(first.getDate() - first.getDay()); // start on Sunday
    return s;
    }
  function endOfCalendar(d: Date) {
    const last = new Date(d.getFullYear(), d.getMonth() + 1, 0);
    const e = new Date(last);
    e.setDate(last.getDate() + (6 - last.getDay())); // end on Saturday
    return e;
  }

  // Build the visible days (6 weeks grid)
  let days: Date[] = [];
  $: {
    const start = startOfCalendar(month);
    const end = endOfCalendar(month);
    const arr: Date[] = [];
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) arr.push(new Date(d));
    days = arr;
  }

  function prevMonth() {
    month = new Date(month.getFullYear(), month.getMonth() - 1, 1);
  }
  function nextMonth() {
    month = new Date(month.getFullYear(), month.getMonth() + 1, 1);
  }

  function toggle(d: Date) {
    const iso = toISO(d);
    const next = new Set(value);
    next.has(iso) ? next.delete(iso) : next.add(iso);
    value = next;
    dispatch('input', next); // enables bind:value
  }

  const isSameMonth = (d: Date, m: Date) => d.getMonth() === m.getMonth() && d.getFullYear() === m.getFullYear();
  const isToday = (d: Date) => {
    const t = new Date();
    return d.getFullYear() === t.getFullYear() && d.getMonth() === t.getMonth() && d.getDate() === t.getDate();
  };
</script>

<div class="rounded-xl border bg-white p-4">
  <div class="mb-3 flex items-center justify-between">
    <button class="rounded px-2 py-1 hover:bg-gray-100" on:click={prevMonth}>‹</button>
    <div class="font-medium">
      {month.toLocaleString(undefined, { month: 'long', year: 'numeric' })}
    </div>
    <button class="rounded px-2 py-1 hover:bg-gray-100" on:click={nextMonth}>›</button>
  </div>

  <div class="grid grid-cols-7 gap-1 text-center text-xs text-gray-500">
    {#each weekDays as w}<div class="py-1">{w}</div>{/each}
  </div>

  <div class="mt-1 grid grid-cols-7 gap-1">
    {#each days as d (d.toDateString())}
      {#key d.getTime()}
        <button
          type="button"
          on:click={() => toggle(d)}
          class="h-9 rounded-md border text-sm transition
            {isSameMonth(d, month) ? 'bg-white' : 'bg-gray-50 text-gray-400'}
            {value.has(toISO(d)) ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-transparent'}
            hover:border-blue-400"
          aria-pressed={value.has(toISO(d))}
          title={toISO(d)}
        >
          <span class="{isToday(d) ? 'rounded-full border border-blue-300 px-2' : ''}">
            {d.getDate()}
          </span>
        </button>
      {/key}
    {/each}
  </div>

  <div class="mt-3 flex items-center justify-between text-sm">
    <div class="truncate text-gray-500">
      {value.size} date{value.size === 1 ? '' : 's'} selected
    </div>
    <button
      type="button"
      class="rounded px-2 py-1 text-gray-600 hover:bg-gray-100"
      on:click={() => { value = new Set(); dispatch('input', value); }}
    >
      Clear
    </button>
  </div>
</div>
