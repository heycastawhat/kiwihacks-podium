<script lang="ts">
  import type { PageData } from "./$types";
  import ProjectCardWrapper from "$lib/components/ProjectCardWrapper.svelte";

  let { data }: { data: PageData } = $props();
</script>

<div class="mx-auto max-w-7xl space-y-5">
  <h1 class="text-5xl font-black tracking-tight text-base-content">Your Projects</h1>

  {#if data.projects.length > 0}
    <div class="grid grid-cols-1 items-start gap-4 md:grid-cols-2 xl:grid-cols-3 md:gap-5">
      {#each data.projects as project (project.id)}
        <div class="w-full max-w-[360px]">
          <ProjectCardWrapper
            {project}
            events={data.events}
          />
        </div>
      {/each}
    </div>
  {:else}
    <div class="py-10 text-center">
      <p class="mb-4 text-base-content/70">
        You haven't submitted any projects yet.
      </p>
      <div class="flex flex-wrap justify-center gap-2">
        <a href="/" class="btn btn-primary">Submit a Project</a>
        <a href="/projects/join" class="btn btn-outline">Join Project</a>
      </div>
    </div>
  {/if}
</div>
