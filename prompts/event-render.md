# Event rendering task

Read the batch file named in your instructions. It contains `events`: a list of
event-render tasks. Write the output file named in your instructions: a JSON
object mapping every `event_id` to its rendered content string.

## Rendering rules

1. Format by `kind`:
   - standup/planning/retro/all_hands: meeting transcript, `name: line` per turn
   - chat: casual channel messages, `name: message` per line
   - dm: two-person direct-message exchange, `name: message` per line
2. Only listed `participants` may speak. Match each speaker's `voice` profile.
3. For every entry in `embed`: its `speaker` must express the `statement` as a
   natural remark, PARAPHRASED (do not copy the sentence verbatim) but
   preserving ALL decidable content — numbers, thresholds, names, direction of
   the rule. The paraphrase must stay within ±2 words of the statement's own
   word count — no added hedges, lead-ins, or trailing clauses inside the
   markers ("I think", "for what it's worth", etc. go OUTSIDE the markers if
   used at all). Wrap exactly the expressing sentence in markers:
   `⟦F-0042⟧the paraphrased sentence⟦/F-0042⟧`. One marker pair per embed, no
   markers anywhere else, never nest markers.
4. Embedded sentences must NOT be emphasized: no exclamation marks, no ALL
   CAPS, no "IMPORTANT"/"NOTE"/bold, not the first line of the event. Each
   embed carries a `position_hint` ("second quarter" / "middle" / "third
   quarter"): place the marked sentence in that region of the event, never
   the first or last line, in the same tone as everything else.
5. If `canary` is set, include the token once, naturally, as a ticket/document
   reference (e.g. "logged as mb-canary-... in the tracker").
6. Length: within `length_words` (total words for the event).
7. Filler content (everything that is not an embedded statement): routine
   status updates, scheduling, logistics, light banter. NEVER invent policies,
   decisions, rules, preferences, or numeric commitments in filler — filler
   must be inert. Do not contradict any embedded statement.
8. Keep tone uniform and businesslike-casual across all events. Vary phrasing;
   no two events should share sentence templates.
