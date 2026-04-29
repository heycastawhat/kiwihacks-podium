<script lang="ts">
  import type { VoteSuspicionResponse } from "$lib/client/types.gen";

  interface Props {
    findings: VoteSuspicionResponse[];
    userLookup: Map<string, string>;
  }

  let { findings, userLookup }: Props = $props();
</script>

<div class="card bg-base-200">
  <div class="card-body">
    <h2 class="card-title">Vote Review ({findings.length})</h2>

    {#if findings.length === 0}
      <p class="text-base-content/70">No suspicious voting patterns found.</p>
    {:else}
      <div class="overflow-x-auto">
        <table class="table table-zebra w-full">
          <thead>
            <tr>
              <th>Signal</th>
              <th>Subject</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {#each findings as finding}
              <tr>
                <td><span class="badge badge-warning">{finding.kind}</span></td>
                <td>
                  {#if finding.voter_id}
                    {userLookup.get(finding.voter_id) || finding.voter_id}
                  {:else}
                    <span class="font-mono text-xs">{finding.ip_address}</span>
                  {/if}
                </td>
                <td>{finding.message}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
