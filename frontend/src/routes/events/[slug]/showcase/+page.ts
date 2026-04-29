import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";
import { client, EventsService } from "$lib/client/sdk.gen";
import type { ProjectPublic } from "$lib/client/types.gen";

export const load: PageLoad = async ({ fetch, parent }) => {
  client.setConfig({ fetch });

  const { event } = await parent();
  const {
    data,
    response,
    error: err,
  } = await EventsService.getEventProjectsEventsEventIdProjectsGet({
    path: {
      event_id: event.id,
    },
    query: {
      leaderboard: event.phase === "closed",
    },
    throwOnError: false,
  });

  if (err || !data) {
    console.error(err, response);
    throw error(response.status, JSON.stringify(err));
  }

  return {
    projects: (data as ProjectPublic[]) ?? [],
  };
};
