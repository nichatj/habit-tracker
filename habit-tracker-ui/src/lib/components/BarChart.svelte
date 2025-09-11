<svelte:options runes={true} />

<script lang="ts">
  // Rune-friendly props (replaces `export let ...`)
  let { labels = [], values = [], height = 220 } =
    $props<{ labels: string[]; values: number[]; height?: number }>();

  // Layout (viewBox units)
  const pad = 6;
  const gap = 2.5;

  // Derived data
  const pairs = $derived(labels.map((lbl, i) => ({
    id: i,                    // unique per bar; avoids duplicate-key crashes
    label: lbl,
    value: values[i] ?? 0
  })));

  const count = $derived(pairs.length);
  const max   = $derived(Math.max(1, ...pairs.map(p => p.value)));
  const barW  = $derived(count ? (100 - pad * 2 - gap * (count - 1)) / count : 0);

  // Deterministic colors (no flicker across renders)
  const colors = $derived(
    Array.from({ length: count }, (_, i) => {
      const hue = (i * 137) % 360; // golden-angle step for nice spread
      return `hsl(${hue} 70% 55%)`;
    })
  );
</script>

<div class="w-full overflow-x-auto">
  <div class="min-w-full">
    <svg class="w-full" {height} viewBox="0 0 100 100" preserveAspectRatio="none">
      <line x1="0" y1="100" x2="100" y2="100" stroke="#e5e7eb" stroke-width="0.5" />
      {#each pairs as p, i (p.id)}
        <rect
          x={pad + i * (barW + gap)}
          y={100 - (p.value / max) * 90}
          width={barW}
          height={(p.value / max) * 90}
          rx="1.5"
          fill={colors[i]}
          stroke="rgba(0,0,0,0.12)"
        >
          <title>{p.label}: {p.value}</title>
        </rect>
      {/each}
    </svg>
  </div>
</div>

{#if pairs.length}
  <ul class="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm text-gray-600">
    {#each pairs as p, i}
      <li class="truncate flex items-center gap-2" title={`${p.label}: ${p.value}`}>
        <span class="inline-block w-3 h-3 rounded-sm border" style={`background:${colors[i]}`}></span>
        <span class="truncate">
          {p.label}: <span class="font-medium text-gray-900">{p.value}</span>
        </span>
      </li>
    {/each}
  </ul>
{/if}
