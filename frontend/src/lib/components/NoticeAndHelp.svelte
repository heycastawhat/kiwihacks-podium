<script lang="ts">
  import { onMount } from "svelte";
  import Modal from "./Modal.svelte";

  let noticeVisible = $state(true);
  let helpModal: Modal = $state() as Modal;

  onMount(() => {
    // Check localStorage for notice preference
    const noticeHidden = localStorage.getItem("podium-notice-hidden");
    if (noticeHidden === "true") {
      noticeVisible = false;
    }
  });

  function dismissNotice() {
    noticeVisible = false;
    localStorage.setItem("podium-notice-hidden", "true");
  }

  function showHelp() {
    helpModal.openModal();
  }
</script>

<!-- Dismissible Notice -->
{#if noticeVisible}
  <div
    class="bg-info text-center rounded-xl max-w-2xl mx-auto mb-6 p-4 relative"
    id="help-notice"
  >
    <button
      onclick={dismissNotice}
      class="btn btn-sm btn-circle btn-ghost absolute top-2 right-2"
      aria-label="Dismiss notice"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-4 w-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
    <p class="text-info-content pr-8">
      If Podium is not working and you need urgent help, ask an organiser for
      help.
    </p>
  </div>
{/if}

<!-- Help Button -->
<div class="fixed bottom-4 right-4 z-50">
  <button
    class="btn btn-info btn-square btn-md font-serif font-light"
    aria-label="Help"
    onclick={showHelp}
  >
    ?
  </button>
</div>

<!-- Help Modal -->
<Modal bind:this={helpModal} title="About Podium">
  <p class="py-4">
    Podium is Kiwihacks's peer-judging platform for hackathons, based on
    Hack Club's podium.
  </p>
  <p class="py-2">
    <strong>Urgent Help:</strong> If Podium is not working and you need
    immediate assistance, ask an organiser for help.
  </p>
</Modal>
