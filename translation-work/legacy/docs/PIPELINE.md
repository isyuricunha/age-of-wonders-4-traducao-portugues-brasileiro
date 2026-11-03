# Pipeline notes

- translation-work.json stores PLAIN text (real newlines/tabs/quotes) in en, pt_old and pt.
  The old escaped convention is gone. Escaping to .po form happens only in build-po (esc()).
- EN/EN.po is generated from EN/EN.MO (mo_convert.py to-po). The .MO is the source of truth
  when the game updates; sync = convert MO -> PO, then refresh work keys (add new, update en,
  clear pt on changed text, keep pt when content is identical modulo line-wrap).
- The game exporter writes real newlines as `\\n` + a line-wrap segment; both EN.po and the
  built PTBR.po follow that style. mo_convert handles it; the .MO binary is the correctness
  reference (real newline byte, never a literal "\n" text).
- Validate: translation_batch.py validate compares token sets (sorted) and \\n counts.
  Merge exits nonzero on mismatch; validate prints and exits 0 (check the output, not the code).
- Capitalization rule (Yuri): first word of every displayed sentence/segment is capitalized,
  unless the sentence opens with a variable/construct token. Name banks (epithets, item adjectives
  like "do Ceifador^a") stay lowercase by design.
