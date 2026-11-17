"""K021, part A (documents only; no code, no model, no selection): Section 6 of the delivered technical document
is extended to the four items the organisers' reply of 3 November 2026 asks for (what happened, affected stages, the
rules snapshot the team worked from, how the selection was re-done) and says what that reply answered. One sentence of
the long document's Section 2 is corrected: the team worked from its old copy of RULES.md until it reviewed the rules
at the end of October, not only "until the 22-23 October clarification".
Sources: the team's e-mail to the organisers of 31 October 2026, the organisers' reply of 3 November 2026 08:40 UTC,
the team's hosted-LLM notice of 3 November 2026 11:08 UTC (all in the team lead's mailbox; read on 16 November 2026,
23:45 Istanbul), rules-provenance.json, REMEDIATION.md, TECHNICAL_DOCUMENT_V2.md Section 2.
The provider-side cleanup is written as the team lead stated it on 16 November 2026, 23:52 (he verified it himself with
another tool); REMEDIATION.md records that statement as his and keeps its earlier dated entries unchanged.
Every replacement must match exactly once. Usage: python3 docs_k021_a.py REPO_DIR"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
SHA = json.loads((REPO / 'rules-provenance.json').read_text())['initial_rules_sha256']
assert len(SHA) == 64 and json.loads((REPO / 'rules-provenance.json').read_text())['initial_rules_snapshot_date'] == '2026-10-20'


def edit(rel, pairs):
    p = REPO / rel
    s = p.read_text(encoding='utf-8')
    for o, n in pairs:
        assert s.count(o) == 1, (rel, s.count(o), o[:100])
        s = s.replace(o, n)
    p.write_text(s, encoding='utf-8')


OLD6 = """## 6. Process disclosure

Before 3 November 2026 the team compared candidates on the public five-minute window, used manual
contact marks from the provided match in diagnostics, and shared extracts of the provided match
with a hosted LLM assistant. The team reported this; the organisers required deletion of those
materials, re-selection of everything on other fixtures, a frozen pipeline and this disclosure.
The submitted system was written from scratch afterwards and uses none of the earlier artefacts;
details, including what could not be verified, are in `TECHNICAL_DOCUMENT_V2.md` Section 2 and
`REMEDIATION.md`. The code of steps 1-8 and 10 was written, and the weights of the network of step 9
were trained, with an AI coding assistant that worked only on source code, public external data and
aggregate external results. The network's design and inference code were written by a team member
on his own branch (`mtah-possession`). The pipeline is run on the provided data locally by the
team.
"""
NEW6 = f"""## 6. Process disclosure

**Rules snapshot.** In October the team worked from a local copy of the organisers' `RULES.md`
dated 20 October 2026 (SHA-256 `{SHA[:8]}...{SHA[-8:]}`, in full in `rules-provenance.json`). Its wording
allowed small amounts of hand-labelled training or validation data. The organisers changed that
wording with their clarification of 22-23 October; the team went on working from its old copy until
it reviewed the rules at the end of October.

**What happened.** In that time the team compared candidate systems on the public five-minute
window and selected versions from those results, used manually identified contact times and ball
points of the provided match in diagnostic validation, and, from about 20 October, shared frame
extracts of the provided match and those notes with a hosted LLM coding assistant (that
conversation stayed in use until 3 November).

**Reported and answered.** The team disclosed this to the organisers by e-mail on 31 October 2026.
Their reply of 3 November says that the wording had been in their own rules until the clarification,
that they see this as a "good-faith situation", and that the team may continue and its submission
will be evaluated as normal on these conditions: delete every hand annotation of the provided match
and anything derived from it; re-make every parameter, threshold and model-version choice on other
matches, without consulting the public window; freeze the pipeline and generate the file
automatically from the repository; disclose the history in this document. They also asked for a
notice of what had been shared with the hosted assistant; it was sent the same day.

**Affected stages.** Parameter and version selection of the pipelines built in October, their
diagnostic validation, and the visual, throw-in and referee prototypes of that time. None of those
artefacts, numbers or code paths is used by the submitted system.

**What was done, condition by condition.**

1. *Delete the hand annotations and everything derived from them.* All of it (786 items, about
   26 GB) was moved out of the project and deleted; its absence was checked on 3 and 7 November.
   The team's existing Git repositories were reviewed: none had one of those files in its tracked
   source. A new repository without the earlier labels, outputs and presets was started.
2. *Re-make every choice on other matches.* The submitted system was written from scratch in the
   new repository. Sections 3 to 5 say for each part on which external matches it was chosen and
   under which registered plan, and name what could not be measured on external data. In the
   delivery chain the public five-minute window is used only after freezing, as a pass/fail check
   that the pipeline runs (Appendix R). Earlier public-window scores are not presented anywhere as
   validation.
3. *Freeze, then generate.* The release is frozen by SHA-256 (every inference source, both tree
   bundles and the network weights) and refuses to run if a file differs. The file is generated
   automatically from the repository by one command; the delivery tool generates it a second time
   and once more from a fresh clone of the pushed branch and compares the bytes (Section 7). The
   run record of the delivered file is Appendix R.
4. *Disclose the history in this document.* This section; more detail in
   `TECHNICAL_DOCUMENT_V2.md` Section 2 and `REMEDIATION.md`.
5. *Hosted assistant.* The notice was sent on 3 November. The conversation was deleted on
   7 November through the application's own control, and the team lead has since verified the
   deletion on the provider's side himself.

**AI assistance in the submitted system.** The code of steps 1-8 and 10 was written, and the
weights of the network of step 9 were trained, with an AI coding assistant that worked only on
source code, public external data and aggregate external results. The network's design and
inference code were written by a team member on his own branch (`mtah-possession`). The pipeline is
run on the provided data locally by the team.
"""
edit('TECHNICAL_DOCUMENT.md', [(OLD6, NEW6)])

edit('TECHNICAL_DOCUMENT_V2.md', [
    (f"""**What happened.** Until the 22-23 October clarification the team worked from a local copy of
`RULES.md` dated 20 October 2026 (SHA-256 `{SHA}`, recorded in
`rules-provenance.json`) whose wording allowed small amounts of hand-labelled training or
validation data. During that period the team (i) compared candidate systems on the public
five-minute window and selected versions from those results, (ii) used manually identified
contact times and ball points from the provided game in diagnostic validation, and (iii) from
about 20 October shared selected frame extracts/screenshots of the provided game and the manual
notes with a hosted LLM coding assistant (OpenAI/Codex). The team disclosed this to the
organisers on 31 October and sent the requested hosted-LLM notice on 3 November.
""",
     f"""**What happened.** In October the team worked from a local copy of
`RULES.md` dated 20 October 2026 (SHA-256 `{SHA}`, recorded in
`rules-provenance.json`) whose wording allowed small amounts of hand-labelled training or
validation data. The organisers changed that wording with their clarification of 22-23 October; the
team went on working from its old copy until it reviewed the rules at the end of October (corrected
on 16 November 2026: this paragraph used to begin "Until the 22-23 October clarification the team
worked from a local copy", which read as if the work described here had ended on that date; the
team's e-mail of 31 October says it had continued from the old copy). During that period the team
(i) compared candidate systems on the public
five-minute window and selected versions from those results, (ii) used manually identified
contact times and ball points from the provided game in diagnostic validation, and (iii) from
about 20 October shared selected frame extracts/screenshots of the provided game and the manual
notes with a hosted LLM coding assistant (OpenAI/Codex; that conversation stayed in use until
3 November). The team disclosed this to the
organisers on 31 October and sent the requested hosted-LLM notice on 3 November. The organisers'
reply of 3 November says that the wording had been in their own rules until the clarification, that
they see this as a "good-faith situation", and that the team may continue and its submission will be
evaluated as normal on the conditions listed at the top of this section.
"""),
])
edit('TECHNICAL_DOCUMENT_V2.md', [
    ("""3 and 7 November). The known provider-side conversation was deleted on 7 November through the
application's control; deletion of separately uploaded files and provider back-end purging could
not be verified (`REMEDIATION.md`). A fresh source repository without legacy labels, outputs or
""",
     """3 and 7 November). The known provider-side conversation was deleted on 7 November through the
application's control, and the team lead has since verified the deletion on the provider's side
himself (`REMEDIATION.md` records both, with their dates). A fresh source repository without legacy labels, outputs or
"""),
])

# (3) the audit record: the earlier entries stay as written; the team lead's statement is added as his statement
p = REPO / 'REMEDIATION.md'
s = p.read_text(encoding='utf-8')
assert s.endswith("Evidence: `C:/Users/Abra/FootballPrivate/remediation-20261103/provider-deletion-20261107.json`.\n") and 'Statement of the team lead' not in s
p.write_text(s + """
## Statement of the team lead — 16 November 2026

On 16 November 2026 the team lead stated that the old conversation is deleted and that he has
since verified the provider's side himself, with a tool other than the assistant that maintains
this repository. That check was not made by, or shown to, the process that maintains this file,
so it is recorded here as his statement; its date and the tool are not recorded here. The entries
above describe what could be checked on their dates and are left as they were written.
""", encoding='utf-8')

# (4) the guidance for agents follows the record
edit('AGENTS.md', [
    ("""- Do not claim all organizer/remediation conditions are complete; provider-side
  conversation/upload cleanup remains unverified in the handoff.
""",
     """- Do not claim more about the organizer/remediation conditions than `REMEDIATION.md` records. The provider-side
  conversation/upload cleanup was verified by the team lead himself (his statement of 16 Nov there), not by an agent.
"""),
])
print('K021 part A written: TECHNICAL_DOCUMENT.md Section 6, TECHNICAL_DOCUMENT_V2.md Section 2, REMEDIATION.md, AGENTS.md')
