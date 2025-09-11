<script lang="ts">
  import "../app.css";
  import favicon from "$lib/assets/favicon.svg";
  import { onMount } from "svelte";

  let { children } = $props();

  // ✅ make it reactive
  let me = $state<{ id: number; email: string } | null>(null);

  async function refreshMe() {
    try {
      const r = await fetch("/api/auth/me", { credentials: "include" });
      if (!r.ok) { me = null; return; }
      const j = await r.json();
      me = j.user ?? null;
    } catch {
      me = null;
    }
  }
  onMount(refreshMe);

  async function logout() {
    try {
      await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    } finally {
      me = null;
      location.href = "/login";
    }
  }
</script>

<!-- Nav -->
<nav class="max-w-5xl mx-auto px-6 py-4 flex items-center gap-4">
  <a href="/" class="font-semibold">Habits</a>
  <a href="/stats" class="text-gray-600 hover:text-gray-900">Stats</a>
  <a href="/calendar" class="text-gray-600 hover:text-gray-900">Calendar</a>
  <div class="ml-auto">
    {#if me}
      <span class="text-sm mr-3">{me.email}</span>
      <!-- ✅ use onclick -->
      <button class="px-3 py-1 rounded bg-gray-200" onclick={logout}>Logout</button>
    {:else}
      <a class="px-3 py-1 rounded bg-blue-400 text-white" href="/login">Login</a>
    {/if}
  </div>
</nav>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

{@render children?.()}
