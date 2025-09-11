<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<!-- Stat, Calendar -->
<nav class="max-w-5xl mx-auto px-6 py-4 flex items-center gap-4">
  <a href="/" class="font-semibold">Habits</a>
  <a href="/stats" class="text-gray-600 hover:text-gray-900">Stats</a>
  <a href="/calendar" class="text-gray-600 hover:text-gray-900">Calendar</a>
</nav>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children?.()}
