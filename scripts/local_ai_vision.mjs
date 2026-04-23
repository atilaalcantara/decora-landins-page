import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { pipeline, env } from '@xenova/transformers';

env.allowRemoteModels = true;
env.allowLocalModels = true;

const EVENT_LABELS = [
  'wedding ceremony',
  'mini wedding',
  '15th birthday party',
  'birthday celebration at home',
  'corporate event',
  'social event reception'
];

const INSTALL_LABELS = [
  'string lights canopy',
  'entrance light tunnel',
  'hanging chandelier lights',
  'illuminated ceiling with fairy lights',
  'illuminated sign letters',
  'filament bulb decoration',
  'outdoor perimeter string lights'
];

const ENV_LABELS = [
  'outdoor garden event',
  'indoor ballroom event',
  'residential backyard event',
  'event entrance corridor',
  'dance floor area',
  'cake table setup'
];

const OBJECT_LABELS = [
  'decorative lights',
  'string lights',
  'light tunnel',
  'chandelier',
  'cake table',
  'ceremony chairs',
  'trees and garden',
  'illuminated sign'
];

const mapLabel = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');

const summarize = (event, install, envLabel, objects) => {
  const objText = objects.slice(0, 3).map(x => x.label).join(', ');
  return `Scene appears to be ${event.label} in a ${envLabel.label}, featuring ${install.label}. Key visual elements: ${objText}.`;
};

const args = Object.fromEntries(
  process.argv.slice(2).map(arg => {
    const [k, v] = arg.split('=');
    return [k.replace(/^--/, ''), v ?? ''];
  })
);

const inputPath = args.input || 'dataset/processed/ai_jobs.json';
const outputPath = args.output || 'dataset/processed/ai_results.json';
const limit = args.limit ? Number(args.limit) : null;

const jobs = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
const queue = limit ? jobs.slice(0, limit) : jobs;

console.log(`AI jobs: ${queue.length}`);
console.log('Loading CLIP zero-shot classifier (local cache after first run)...');

const classifier = await pipeline('zero-shot-image-classification', 'Xenova/clip-vit-base-patch32');

const results = [];
let count = 0;
for (const job of queue) {
  const imagePath = path.resolve(job.image_path);
  try {
    const [events, installs, envs, objects] = await Promise.all([
      classifier(imagePath, EVENT_LABELS, { topk: 3 }),
      classifier(imagePath, INSTALL_LABELS, { topk: 3 }),
      classifier(imagePath, ENV_LABELS, { topk: 3 }),
      classifier(imagePath, OBJECT_LABELS, { topk: 4 }),
    ]);

    const topEvent = events[0];
    const topInstall = installs[0];
    const topEnv = envs[0];

    results.push({
      id: job.id,
      ai_description: summarize(topEvent, topInstall, topEnv, objects),
      ai_predictions: {
        event: events.map(x => ({ label: mapLabel(x.label), score: Number(x.score.toFixed(4)) })),
        installation: installs.map(x => ({ label: mapLabel(x.label), score: Number(x.score.toFixed(4)) })),
        environment: envs.map(x => ({ label: mapLabel(x.label), score: Number(x.score.toFixed(4)) })),
        objects: objects.map(x => ({ label: mapLabel(x.label), score: Number(x.score.toFixed(4)) })),
      }
    });
  } catch (err) {
    results.push({
      id: job.id,
      ai_error: err?.message || 'ai_inference_error',
      ai_description: 'AI analysis unavailable for this image.',
      ai_predictions: { event: [], installation: [], environment: [], objects: [] }
    });
  }

  count += 1;
  if (count % 25 === 0 || count === queue.length) {
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf-8');
    console.log(`Processed ${count}/${queue.length}`);
  }
}

fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf-8');
console.log(`Saved: ${outputPath}`);
