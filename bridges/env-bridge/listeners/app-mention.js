import { enqueueCommand } from '../lib/enqueue.js';

export async function appMention({ event, say, logger }) {
  const text = event.text.replace(/<@[^>]+>/g, '').trim();
  if (!text) return;
  await enqueueCommand(
    {
      command: text,
      channel: event.channel,
      thread_ts: event.thread_ts ?? event.ts,
      user: event.user,
      via: 'mention',
    },
    logger,
  );
  await say({
    thread_ts: event.thread_ts ?? event.ts,
    text: `:hourglass_flowing_sand: on it — \`${text}\``,
  });
}
