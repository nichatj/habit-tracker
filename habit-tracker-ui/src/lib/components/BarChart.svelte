<script lang="ts">
  export let labels: string[] = [];
  export let values: number[] = [];
  export let height = 220;

  // Keep your single, ordered array
  $: pairs = labels.map((lbl, i) => ({ label: lbl, value: values[i] ?? 0 }));

  // Layout numbers (viewBox units)
  const pad = 6;
  const gap = 2.5;
  $: max   = Math.max(1, ...pairs.map(p => p.value));
  $: count = pairs.length;
  $: barW  = count ? (100 - pad * 2 - gap * (count - 1)) / count : 0;

  // ---- distinct random colors per bar ----
  let colors: string[] = [];

  // regenerate only if bar count changes
  $: if (count !== colors.length) {
    // pick a random starting hue, then spread hues evenly around the circle
    const offset = Math.floor(Math.random() * 360);
    colors = Array.from({ length: count }, (_, i) => {
      const hue = (offset + Math.round(360 / Math.max(1, count)) * i) % 360;
      return `hsl(${hue} 70% 55%)`;
    });
    // optional shuffle so the order isn't correlated with index
    shuffle(colors);
  }

  function shuffle(a: string[]) {
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
  }
</script>

<div class="w-full overflow-x-auto">
  <div class="min-w-full">
    <svg class="w-full" {height} viewBox="0 0 100 100" preserveAspectRatio="none">
      <line x1="0" y1="100" x2="100" y2="100" stroke="#e5e7eb" stroke-width="0.5" />
      {#each pairs as p, i (p.label)}
        <rect
          x={pad + i * (barW + gap)}
          y={100 - (p.value / max) * 90}
          width={barW}
          height={(p.value / max) * 90}
          rx="1.5"
          fill={colors[i] /* distinct random color */}
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
