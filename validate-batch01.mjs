#!/usr/bin/env node
import { readFileSync } from 'fs';

const BATCH_PATH = '/Users/radiohead/Dev/memory-bench/datasets/dev/org-00004-twin/render/batch-01.json';
const OUT_PATH = '/Users/radiohead/Dev/memory-bench/datasets/dev/org-00004-twin/render/batch-01.out.json';

const issues = [];
const embedStats = [];

function wordCount(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function stripMarkers(text) {
  return text.replace(/⟦F-\d{4}⟧([\s\S]*?)⟦\/F-\d{4}⟧/g, '$1');
}

function countWordsWithMarkersStripped(text) {
  return wordCount(stripMarkers(text));
}

// Check 11: Valid JSON
let batch, out;
try {
  batch = JSON.parse(readFileSync(BATCH_PATH, 'utf8'));
} catch (e) {
  issues.push(`[JSON] batch-01.json is invalid JSON: ${e.message}`);
  console.log('=== VALIDATION RESULTS ===\n');
  for (const issue of issues) console.log(issue);
  console.log('\nISSUES FOUND');
  process.exit(1);
}

try {
  out = JSON.parse(readFileSync(OUT_PATH, 'utf8'));
} catch (e) {
  issues.push(`[JSON] batch-01.out.json is invalid JSON: ${e.message}`);
  console.log('=== VALIDATION RESULTS ===\n');
  for (const issue of issues) console.log(issue);
  console.log('\nISSUES FOUND');
  process.exit(1);
}

const batchEventIds = batch.events.map((e) => e.event_id);
const outEventIds = Object.keys(out);

// Check 1: event_id parity
const batchSet = new Set(batchEventIds);
const outSet = new Set(outEventIds);

for (const id of batchEventIds) {
  if (!outSet.has(id)) {
    issues.push(`[event_ids] ${id} in batch but missing from out`);
  }
}
for (const id of outEventIds) {
  if (!batchSet.has(id)) {
    issues.push(`[event_ids] ${id} in out but not in batch (extra)`);
  }
}

for (const event of batch.events) {
  const { event_id, participants, embed, length_words } = event;
  const text = out[event_id];

  if (text === undefined) continue;

  const participantNames = new Set(participants.map((p) => p.name));
  const lines = text.split('\n');
  const [lo, hi] = length_words ?? [0, Infinity];

  // Check 2: Word count within length_words
  const eventWordCount = countWordsWithMarkersStripped(text);
  if (eventWordCount < lo || eventWordCount > hi) {
    issues.push(
      `[length_words] ${event_id}: event word count ${eventWordCount} outside [${lo}, ${hi}]`
    );
  }

  // Check 10: One marker pair per embed, no nesting
  const openMatches = [...text.matchAll(/⟦F-\d{4}⟧/g)];
  const closeMatches = [...text.matchAll(/⟦\/F-\d{4}⟧/g)];
  const embedLen = embed?.length ?? 0;
  if (openMatches.length !== embedLen || closeMatches.length !== embedLen) {
    issues.push(
      `[markers] ${event_id}: open=${openMatches.length}, close=${closeMatches.length}, embed=${embedLen} (must all match)`
    );
  }

  // Check nesting: scan for nested opens before close
  const markerTokenRe = /⟦\/?F-\d{4}⟧/g;
  let depth = 0;
  let maxDepth = 0;
  let m;
  while ((m = markerTokenRe.exec(text)) !== null) {
    if (m[0].startsWith('⟦/')) {
      depth--;
      if (depth < 0) {
        issues.push(`[markers] ${event_id}: unmatched close marker at index ${m.index}`);
        depth = 0;
      }
    } else {
      depth++;
      maxDepth = Math.max(maxDepth, depth);
    }
  }
  if (depth !== 0) {
    issues.push(`[markers] ${event_id}: unbalanced markers (depth=${depth} at end)`);
  }
  if (maxDepth > 1) {
    issues.push(`[markers] ${event_id}: nested markers detected (max depth=${maxDepth})`);
  }

  // Extract markers in order
  const markerRe = /⟦(F-\d{4})⟧([\s\S]*?)⟦\/\1⟧/g;
  const foundMarkers = [];
  let match;
  while ((match = markerRe.exec(text)) !== null) {
    foundMarkers.push({
      fact_id: match[1],
      paraphrase: match[2],
      fullMatch: match[0],
      index: match.index,
    });
  }

  // Check 3: Marker fact_ids in same order as embed array
  const expectedOrder = embed.map((e) => e.fact_id);
  const foundOrder = foundMarkers.map((m) => m.fact_id);
  if (JSON.stringify(expectedOrder) !== JSON.stringify(foundOrder)) {
    issues.push(
      `[order] ${event_id}: marker order [${foundOrder.join(', ')}] != embed order [${expectedOrder.join(', ')}]`
    );
  }

  // Map line index to content for position checks
  const lineStarts = [];
  let pos = 0;
  for (const line of lines) {
    lineStarts.push(pos);
    pos += line.length + 1;
  }

  function lineIndexForCharIndex(charIndex) {
    for (let i = lineStarts.length - 1; i >= 0; i--) {
      if (charIndex >= lineStarts[i]) return i;
    }
    return 0;
  }

  for (let i = 0; i < embed.length; i++) {
    const emb = embed[i];
    const marker = foundMarkers[i];
    const label = `${event_id}/${emb.fact_id}`;

    if (!marker) {
      issues.push(`[embed] ${label}: marker not found`);
      continue;
    }

    const statementForCount = emb.statement.replace(/\.$/, '');
    const stmtWords = wordCount(statementForCount);
    const paraWords = wordCount(marker.paraphrase);
    const delta = paraWords - stmtWords;

    embedStats.push({
      event_id,
      fact_id: emb.fact_id,
      statement_words: stmtWords,
      paraphrase_words: paraWords,
      delta,
    });

    // Check 8: Paraphrase word count within ±2 of statement
    if (Math.abs(delta) > 2) {
      issues.push(
        `[word_delta] ${label}: paraphrase=${paraWords}, statement=${stmtWords}, delta=${delta} (must be within ±2)`
      );
    }

    // Check 7: Statement must NOT appear verbatim in text
    if (text.includes(emb.statement)) {
      issues.push(`[verbatim] ${label}: statement appears verbatim in event text`);
    }

    // Check 9: Forbidden content inside markers
    const para = marker.paraphrase;
    if (para.includes('!')) {
      issues.push(`[forbidden] ${label}: contains '!' inside marker`);
    }
    if (para.includes('**')) {
      issues.push(`[forbidden] ${label}: contains '**' inside marker`);
    }
    if (/\bIMPORTANT\b/.test(para)) {
      issues.push(`[forbidden] ${label}: contains IMPORTANT inside marker`);
    }
    if (/\bREMINDER\b/.test(para)) {
      issues.push(`[forbidden] ${label}: contains REMINDER inside marker`);
    }
    if (/\bNOTE:\b/.test(para)) {
      issues.push(`[forbidden] ${label}: contains NOTE: inside marker`);
    }
    const capsMatches = [...para.matchAll(/\b[A-Z]{4,}\b/g)];
    for (const cm of capsMatches) {
      issues.push(`[forbidden] ${label}: ALL-CAPS word "${cm[0]}" inside marker`);
    }

    // Find the line containing this marker
    const markerLineIdx = lineIndexForCharIndex(marker.index);
    const markerLine = lines[markerLineIdx];

    // Check 5: Embedded sentences must NOT be on first or last line
    if (markerLineIdx === 0) {
      issues.push(`[position] ${label}: marker on first line of event`);
    }
    if (markerLineIdx === lines.length - 1) {
      issues.push(`[position] ${label}: marker on last line of event`);
    }

    // Check 6: Speaker of marked line must match embed.speaker
    const colonIdx = markerLine.indexOf(':');
    if (colonIdx === -1) {
      issues.push(`[speaker] ${label}: marked line has no speaker (no colon)`);
    } else {
      const speaker = markerLine.slice(0, colonIdx).trim();
      if (speaker !== emb.speaker) {
        issues.push(
          `[speaker] ${label}: line speaker "${speaker}" != embed.speaker "${emb.speaker}"`
        );
      }
    }
  }

  // Check 4: Only participants may speak
  for (let li = 0; li < lines.length; li++) {
    const line = lines[li];
    const colonIdx = line.indexOf(':');
    if (colonIdx === -1) {
      issues.push(`[participants] ${event_id} line ${li + 1}: no speaker delimiter ':'`);
      continue;
    }
    const speaker = line.slice(0, colonIdx).trim();
    if (!participantNames.has(speaker)) {
      issues.push(
        `[participants] ${event_id} line ${li + 1}: speaker "${speaker}" is not a participant`
      );
    }
  }
}

// Print results
console.log('=== VALIDATION RESULTS ===\n');

console.log('--- Per-event word counts (markers stripped) ---');
for (const event of batch.events) {
  const text = out[event.event_id];
  if (text === undefined) continue;
  const wc = countWordsWithMarkersStripped(text);
  const [lo, hi] = event.length_words ?? [0, Infinity];
  const ok = wc >= lo && wc <= hi ? 'OK' : 'OUT OF RANGE';
  console.log(`${event.event_id}: ${wc} words [${lo}, ${hi}] ${ok}`);
}

console.log('\n--- Per-embed word counts ---');
for (const s of embedStats) {
  const ok = Math.abs(s.delta) <= 2 ? 'OK' : 'DELTA OUT OF RANGE';
  console.log(
    `${s.event_id}/${s.fact_id}: statement=${s.statement_words}, paraphrase=${s.paraphrase_words}, delta=${s.delta >= 0 ? '+' : ''}${s.delta} ${ok}`
  );
}

if (issues.length > 0) {
  console.log('\n--- Issues ---');
  for (const issue of issues) {
    console.log(issue);
  }
  console.log('\nISSUES FOUND');
} else {
  console.log('\nALL OK');
}
