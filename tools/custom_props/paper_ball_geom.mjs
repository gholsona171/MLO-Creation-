// Dumps one paper-ball shape from a crumple simulation module (c9_stickynotes web/src/lib/crumple/sim.js) as JSON, so the
// world prop is the same crumpled sheet the UI shows.  node paper_ball_geom.mjs <sim.js> <n> <seed> > ball.json
import { pathToFileURL } from 'node:url';
const [simPath, n = '12', seed = '7'] = process.argv.slice(2);
const { buildCrumple } = await import(pathToFileURL(simPath).href);
const sim = buildCrumple({ n: Number(n), seed: Number(seed), ballFrames: 40, unfoldFrames: 2 });
const ball = sim.ball[sim.ball.length - 1];
process.stdout.write(JSON.stringify({ n: sim.n, pos: Array.from(ball), uv: Array.from(sim.uv), index: Array.from(sim.index) }));
