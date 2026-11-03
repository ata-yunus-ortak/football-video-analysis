# Technical report — remediation release

## Prior process and organizer clarification

Development initially relied on a local 20 October 2026 rules snapshot whose
wording allowed small amounts of hand-labelled training/validation data. The
22–23 October clarification prohibited human annotations of the supplied fixture
for those purposes and public-window parameter/model selection.

The affected earlier process included repeated public-window comparisons,
version selection using those results, manual contact-time and ball-point
diagnostics, and some match-frame inspection through a hosted coding assistant.
These are development/selection and data-sharing issues; automatic final
inference alone did not remove their influence.

The organizer replied on 3 November 2026 that participation may continue if
general ideas are retained while hand annotations and derivatives are removed,
all choices are re-made on other fixtures, the pipeline is frozen and the full
match is regenerated automatically, and this history is disclosed. Earlier
public-window scores are not validation and are not used in this report.

The source/correspondence hashes and completion status are recorded in the
private remediation audit. This report does not reproduce any match annotations.

## Current inference

Automatic player/ball x/y and metadata team membership determine distances to
each team's nearest observed player. The selected temporal policy requires
external-data-selected proximity, separation and confirmation support. It can
backdate a subsequently confirmed run to its first supporting observation and
hold an owner only for a bounded externally selected period. Unknown is X.

The selected policy and numerical choices are in model.json. The calibration
frame rate is recorded there; temporal frame counts are converted using the
actual input frame rate. The EPTS third coordinate channel is not interpreted as
height. Half/kickoff/contact clocks from human review are not inputs.

## Reselection

The previous numerical configuration was not copied. Other-fixture SkillCorner
automatic measurements and possession estimates were used to construct and
compare candidates. A deterministic, registered match split separated twelve
calibration fixtures from four validation fixtures. Since those external games
had been used in earlier external studies, this is disclosed as development
reuse, not an untouched test.

The choices compared include nearest, player-run and team-run temporal evidence,
measured versus estimated votes, externally derived control/separation distances,
confirmation/hold lengths and bounded interpolation versus no interpolation.
Model code and data hashes were fixed around selection; the supplied fixture
and its public reference were not consulted for candidate ranking.

Four additional fixtures were reserved before download. Their model predictions
are generated after the selection freeze and frozen before proxy evaluation.
No result from that check may change this release. The study's team-spell and
H/A macro metrics measure agreement with an automatic provider, not official
possession accuracy or the challenge's full-match Spell F1.

That four-match check completed with mean automatic-provider team-spell proxy
0.17491946, H/A macro F1 0.63910663 and known-teacher-frame agreement 0.53943456.
All four prediction files were frozen before proxy evaluation. No model
parameter, policy or inference-source byte changed in response to these results.
The aggregate report is external-check.json.

## Features not promoted

General image/limb/throw/replacement/referee and retrospective-boundary ideas are
retained as unselected prototypes outside this repository. Their engineering
presets have not all been reselected using labelled/evaluable other-fixture
visual and D evidence. They are excluded from this frozen release rather than
represented as independently validated. That selection and a later release
remain separate work. No manual supplied-fixture annotations are permitted for it.

This H/A/X release cannot claim complete dead-ball recognition. A provider's
unknown ownership is not evidence of D. The absence of an independently selected
D layer is a material performance limitation, not hidden by an old public score.

## Reproducibility and compliance status

The local Git source is committed before full-match inference. model.json records
the source hashes checked on execution. Generated match data stays outside the
repository. The full file is regenerated from raw automatic coordinates and
metadata, with every input frame represented; format/alignment checks do not
rank candidates on the public reference.

The 199,319-row full-match file passed structural validation and a second
generation produced the identical CSV hash. This is reproducibility evidence,
not possession accuracy. Git attributes preserve exact frozen source bytes
across line-ending settings; a storage-format correction did not change model
parameters or local inference-source bytes.

The source repository has no annotation-bearing earlier history and no remote
push was performed. Legacy affected artifacts were removed from active project
paths into a separately identified pending-deletion directory. The tool blocked
permanent deletion, and the user then reported permanently deleting that
directory on 3 November. A local check confirmed the exact path was absent.
This is user attestation plus a path check, not verification of every disk or
backup copy. The historical staging and tool-refusal records are retained.

A hosted-LLM notice was sent to the organizer on 3 November, describing the
categories and period of sharing and honestly stating that provider deletion
was pending. The affected active conversation and available provider-side
uploads must still be deleted using the available controls. This document does
not claim provider records or backups have been erased, or that all conditions
are already satisfied.
