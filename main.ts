// main.ts — news-image-20261121 entry: "The Saturday Globe".
//
// Copies the pre-rendered entry.png (drawn by draw.py, PIL,
// deterministic) to $MAKEFUN_OUTPUT_DIR (default /output).
// Node 22, stdlib only, no network.
//
// Entry: 37 stories from Saturday 21 November 2026 across 8 continents
// (Asia 11, Europe 7, North America 7, South America 4, Africa 4,
// Oceania 2, Zealandia 1, Antarctica 1) — 13 illustrated panels plus a
// 24-story briefs list and a pinned world map. A midnight-navy
// "night desk" front page: deep navy page, cream story cards, gold
// rules, Anton masthead, Montserrat labels, red chips.
// Render verified deterministic: draw.py run twice gives
// byte-identical entry.png (1024x1024, 698505 bytes).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR || "/output";
mkdirSync(outDir, { recursive: true });
copyFileSync(join(here, "entry.png"), join(outDir, "entry.png"));
