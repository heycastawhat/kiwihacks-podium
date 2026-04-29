<script lang="ts">
  import UpdateProjectModal from "./UpdateProjectModal.svelte";
  import Modal from "./Modal.svelte";
  import type { EventPrivate, EventPublic, ProjectPrivate } from "$lib/client/types.gen";
  import { validateProject } from "$lib/validation";
  import { customInvalidateAll } from "$lib/misc";
  import { toast } from "svelte-sonner";
  import { client } from "$lib/client/sdk.gen";
  import { getAuthenticatedUser } from "$lib/user.svelte";

  interface Props {
    project: ProjectPrivate;
    events: Array<EventPrivate | EventPublic>;
  }

  let { project, events }: Props = $props();

  let editModal = $state<Modal>();
  let validationModal = $state<Modal>();
  let revalidating = $state(false);
  let imageReady = $state(false);
  let imageFailed = $state(false);
  let teamBusy = $state(false);

  const eventForProject = $derived(
    events.find((event) => event.id === project.event_id)
  );

  const credits = $derived.by(() => {
    const allNames = [
      project.owner_display_name,
      ...(project.collaborator_display_names ?? []),
    ].filter((name): name is string => Boolean(name));

    if (allNames.length === 0) return "Unknown contributors";

    const formatter = new Intl.ListFormat("en", {
      style: "short",
      type: "conjunction",
    });
    return formatter.format(allNames);
  });

  const collaboratorEntries = $derived.by(() => {
    const ids = project.collaborator_ids ?? [];
    const names = project.collaborator_display_names ?? [];
    return ids.map((id, index) => ({
      id,
      name: names[index] || id,
    }));
  });

  const isOwner = $derived(project.owner_id === getAuthenticatedUser().user.id);
  const currentCollaborator = $derived(
    collaboratorEntries.find((collaborator) => collaborator.id === getAuthenticatedUser().user.id)
  );

  const statusBadge = $derived(
    project.validation_status === "valid"
      ? { cls: "badge-success", label: "Valid", icon: "✅" }
      : project.validation_status === "warning"
        ? { cls: "badge-warning", label: "Warning", icon: "⚠️" }
        : { cls: "badge-neutral", label: "Pending", icon: "⏳" }
  );

  async function triggerRevalidation() {
    revalidating = true;
    try {
      await validateProject(project.id);
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await customInvalidateAll();
    } finally {
      revalidating = false;
    }
  }

  async function copyJoinCode() {
    try {
      await navigator.clipboard.writeText(project.join_code);
      toast.success("Join code copied");
    } catch (err) {
      console.error("Failed to copy join code", err);
      toast.error("Could not copy join code");
    }
  }

  async function copyInviteLink() {
    const path = `/projects/join?join_code=${encodeURIComponent(project.join_code)}`;
    const inviteUrl = new URL(path, window.location.origin).toString();
    try {
      await navigator.clipboard.writeText(inviteUrl);
      toast.success("Invite link copied");
    } catch (err) {
      console.error("Failed to copy invite link", err);
      toast.error("Could not copy invite link");
    }
  }

  async function removeCollaborator(userId: string) {
    teamBusy = true;
    try {
      const { error } = await client.delete({
        url: `/projects/${project.id}/collaborators/${userId}`,
      });
      if (error) {
        toast.error(typeof error === "string" ? error : "Could not update team");
        return;
      }
      toast.success(userId === getAuthenticatedUser().user.id ? "Left project" : "Collaborator removed");
      await customInvalidateAll();
    } finally {
      teamBusy = false;
    }
  }

  async function transferOwner(userId: string) {
    teamBusy = true;
    try {
      const { error } = await client.post({
        url: `/projects/${project.id}/transfer-owner`,
        body: { new_owner_id: userId },
      });
      if (error) {
        toast.error(typeof error === "string" ? error : "Could not transfer owner");
        return;
      }
      toast.success("Owner transferred");
      await customInvalidateAll();
    } finally {
      teamBusy = false;
    }
  }
</script>

<div class="h-full rounded-[28px] border-2 border-dashed border-base-content/35 bg-base-100/85 p-4 shadow-sm">
  <div class="space-y-3">
    <div class="text-center">
      <p class="text-xs font-semibold uppercase tracking-wide text-base-content/55">Event Name</p>
      {#if eventForProject}
        <a
          href={`/events/${eventForProject.slug}`}
          class="link link-hover text-base font-semibold text-base-content"
          data-sveltekit-noscroll
        >
          {eventForProject.name}
        </a>
      {:else}
        <p class="text-sm text-base-content/60">Unknown event</p>
      {/if}
    </div>

    <div class="grid grid-cols-1 gap-2 rounded-2xl border border-base-content/20 bg-base-100/70 p-2 text-center sm:grid-cols-3">
      <div>
        <p class="text-[10px] uppercase tracking-wide text-base-content/55">Status</p>
        {#if revalidating}
          <span class="badge badge-sm badge-neutral mt-1">
            <span class="loading loading-dots loading-xs"></span>
          </span>
        {:else}
          <button
            class={`badge badge-sm mt-1 border border-base-content/20 ${statusBadge.cls}`}
            onclick={() => validationModal?.openModal()}
          >
            {statusBadge.icon} {statusBadge.label}
          </button>
        {/if}
      </div>

      <div>
        <p class="text-[10px] uppercase tracking-wide text-base-content/55">Join Code</p>
        <div class="mt-1 flex flex-wrap justify-center gap-1">
          <button
            type="button"
            class="badge badge-sm badge-outline font-mono cursor-copy"
            onclick={copyJoinCode}
            title="Click to copy join code"
          >
            {project.join_code}
          </button>
          <button
            type="button"
            class="badge badge-sm badge-outline cursor-copy"
            onclick={copyInviteLink}
            title="Copy invite link"
          >
            Invite
          </button>
        </div>
      </div>

      <div>
        <p class="text-[10px] uppercase tracking-wide text-base-content/55">Actions</p>
        <button
          class="btn btn-xs btn-outline mt-1"
          onclick={() => editModal?.openModal()}
        >
          Edit
        </button>
      </div>
    </div>

    <div class="rounded-[22px] border-2 border-dashed border-base-content/35 p-3">
      <p class="text-center text-xs font-semibold uppercase tracking-wide text-base-content/55">Project</p>

      <div class="mt-2 overflow-hidden rounded-xl border border-base-content/15 bg-base-200/40">
        {#if project.image_url}
          <img
            src={project.image_url}
            alt={project.name}
            class="aspect-[3/2] w-full object-cover"
            loading="lazy"
            onload={() => (imageReady = true)}
            onerror={() => {
              imageReady = true;
              imageFailed = true;
            }}
            style={`opacity: ${imageReady && !imageFailed ? 1 : 0}; transition: opacity 180ms ease;`}
          />
        {/if}

        {#if project.image_url && !imageReady}
          <div class="skeleton aspect-[3/2] w-full"></div>
        {:else if !project.image_url || imageFailed}
          <div class="flex aspect-[3/2] items-center justify-center text-sm text-base-content/50">
            No image
          </div>
        {/if}
      </div>

      <div class="mt-3 border-t border-base-content/20 pt-3 text-center">
        <h3 class="text-lg font-semibold leading-tight text-base-content">{project.name}</h3>
        <p class="mt-2 line-clamp-2 text-sm text-base-content/75">
          {project.description || "No description yet."}
        </p>
        <p class="mt-2 text-xs text-base-content/60">{credits}</p>
      </div>

      <div class="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
        <a
          href={project.repo}
          target="_blank"
          rel="noopener noreferrer"
          class="btn btn-sm btn-info"
        >
          Repo
        </a>

        {#if project.demo}
          <a
            href={project.demo}
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-sm btn-success"
          >
            Demo
          </a>
        {:else}
          <span class="btn btn-sm btn-disabled">Demo</span>
        {/if}

        <button class="btn btn-sm btn-outline" onclick={() => editModal?.openModal()}>
          Edit
        </button>
      </div>

      {#if isOwner || currentCollaborator}
        <div class="mt-4 rounded-xl border border-base-content/15 bg-base-100/70 p-3 text-left">
          <p class="text-xs font-semibold uppercase tracking-wide text-base-content/55">Team</p>
          {#if collaboratorEntries.length === 0}
            <p class="mt-2 text-sm text-base-content/60">No collaborators yet.</p>
          {:else}
            <div class="mt-2 space-y-2">
              {#each collaboratorEntries as collaborator}
                <div class="flex items-center justify-between gap-2">
                  <span class="min-w-0 truncate text-sm">{collaborator.name}</span>
                  <div class="flex shrink-0 gap-1">
                    {#if isOwner}
                      <button
                        class="btn btn-xs btn-outline"
                        onclick={() => transferOwner(collaborator.id)}
                        disabled={teamBusy}
                      >
                        Make owner
                      </button>
                    {/if}
                    {#if isOwner || collaborator.id === currentCollaborator?.id}
                      <button
                        class="btn btn-xs btn-error btn-outline"
                        onclick={() => removeCollaborator(collaborator.id)}
                        disabled={teamBusy}
                      >
                        {collaborator.id === currentCollaborator?.id ? "Leave" : "Remove"}
                      </button>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>
</div>

<Modal title="Validation Details" bind:this={validationModal}>
  <div class="space-y-4">
    <div class="flex items-center gap-2 mb-2">
      {#if project.validation_status === "valid"}
        <span class="text-success text-lg">✅ Your project looks good!</span>
      {:else if project.validation_status === "warning"}
        <span class="text-warning text-lg">⚠️ Potential issue detected</span>
      {:else}
        <span class="text-base-content/70 text-lg">Validation pending…</span>
      {/if}
    </div>
    {#if project.validation_message}
      <p class="text-sm text-base-content/70">{project.validation_message}</p>
    {/if}
    <p class="text-xs text-base-content/50">
      Validation warnings are informational - your project is never blocked.
    </p>
    <button
      class="btn btn-sm btn-outline"
      onclick={triggerRevalidation}
      disabled={revalidating}
    >
      {revalidating ? "Re-validating…" : "Re-validate"}
    </button>
  </div>
</Modal>

<UpdateProjectModal preselectedProject={project} {events} bind:modal={editModal} />
