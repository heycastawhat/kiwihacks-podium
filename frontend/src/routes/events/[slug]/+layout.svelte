<script lang="ts">
  let { children, data } = $props();

  const eventHeroImages: Record<string, string> = {
    kiwihacks: "/assets/kiwihacks/kiwi-text.png",
  };

  const eventHeroImage = $derived.by(() => {
    const slugImage = eventHeroImages[data.event.slug];
    if (slugImage) return slugImage;
    if (data.event.name.toLowerCase().includes("kiwihacks")) {
      return eventHeroImages.kiwihacks;
    }
    return "";
  });
</script>

{#if eventHeroImage}
  <div class="flex justify-center pt-6 pb-2">
    <img
      src={eventHeroImage}
      alt={data.event.name}
      class="h-28 object-contain"
    />
  </div>
{/if}

<div class="text-center p-4 space-y-1">
  <h1 class="text-2xl font-semibold">
    <a href="/events/{data.event.slug}" class="link hover-link">
      {data.event.name}
    </a>
  </h1>
  <p class="mono text-base-content/80">{data.event.description}</p>
</div>

{@render children()}
