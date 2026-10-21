<!-- Location-only follow-up inventory for the public payload; reviewers use it to scope separately owned remediation. -->
# Public exposure follow-up

Scope: all tracked files plus nonignored new files, read from the current working tree.
The scan uses registered seat IDs, private project inventory tokens, personal/site identity terms, machine paths, cloud identifiers, and concrete private dispatch references.
A supplementary search inspected repository URLs, email addresses, deployment domains, and home paths.
No matched identifying value is reproduced here.
The two sanitized JSON artifacts contain no matches in the identifier categories checked.
The design was separately generalized after semantic review; this does not establish that every supporting artifact is safe to publish.
Historical research scores and labels remain usable; sanitized summaries cannot reproduce the original private-text inference.

## Remediation owned by a separate task

Operational scripts, behavior-bearing policy data, test fixtures, and research prototypes are unchanged.
The saved catalogue output is generated historical evidence and is listed for owner-led regeneration or replacement.
The identifier scan and supplementary semantic review have different coverage.
This inventory records discovered locations, including corrected documentation locations; it is not an exhaustive guarantee about private context, unknown secrets or Git history.

| Location | Category |
| --- | --- |
| `agentmail/bin/agentmail-launch:53` | person_or_site_identity |
| `agentmail/bin/agentmail-launch:54` | person_or_site_identity, seat_identity |
| `agentmail/bin/agentmail-launch:304` | private_project_reference |
| `agentmail/bin/agentmail-launch:309` | person_or_site_identity |
| `agentmail/bin/agentmail-launch:354` | person_or_site_identity |
| `agentmail/bin/agentmail-launch:355` | person_or_site_identity |
| `agentmail/bin/agentmail-launch:360` | person_or_site_identity, private_operational_reference |
| `agentmail/bin/agentmail-launch:413` | private_operational_reference, private_project_reference |
| `agentmail/bin/agentmail-launch:416` | private_project_reference |
| `agentmail/bin/agentmail-launch:425` | private_project_reference |
| `agentmail/bin/agentmail-launch:426` | private_project_reference |
| `agentmail/bin/change-report:5` | person_or_site_identity |
| `agentmail/bin/codex-models:7` | person_or_site_identity |
| `agentmail/bin/fleet-guard:8` | person_or_site_identity, seat_identity |
| `agentmail/bin/fleet-guard:20` | person_or_site_identity |
| `agentmail/bin/fleet-guard:26` | machine_path, person_or_site_identity, private_project_reference |
| `agentmail/bin/fleet-guard:27` | person_or_site_identity, seat_identity |
| `agentmail/bin/fleet-guard:68` | person_or_site_identity |
| `agentmail/bin/fleet-guard:76` | person_or_site_identity |
| `agentmail/bin/fleet-guard:97` | person_or_site_identity |
| `agentmail/bin/fleet-start.command:4` | person_or_site_identity |
| `agentmail/bin/fleet-start.command:12` | machine_path, person_or_site_identity, private_project_reference |
| `agentmail/bin/fleet-start.command:14` | person_or_site_identity, seat_identity |
| `agentmail/bin/fleet-start.command:41` | person_or_site_identity, seat_identity |
| `agentmail/bin/overseer-astra.command:4` | machine_path, person_or_site_identity, private_project_reference |
| `agentmail/bin/overseer-astra.command:7` | machine_path, person_or_site_identity, private_project_reference |
| `agentmail/bin/overseer-astra.command:9` | machine_path, person_or_site_identity, private_project_reference, seat_identity |
| `agentmail/bin/overseer-codex.command:4` | person_or_site_identity |
| `agentmail/bin/overseer-codex.command:7` | machine_path, person_or_site_identity, private_project_reference |
| `agentmail/bin/overseer-codex.command:11` | machine_path, person_or_site_identity, private_project_reference |
| `agentmail/bin/overseer-codex.command:14` | person_or_site_identity, seat_identity |
| `agentmail/bin/project-map:5` | person_or_site_identity |
| `agentmail/lib/model_guard.py:20` | person_or_site_identity, seat_identity |
| `agentmail/lib/model_guard.py:21` | person_or_site_identity |
| `agentmail/lib/model_guard.py:29` | person_or_site_identity, seat_identity |
| `agentmail/lib/security_lock_patterns.txt:5` | person_or_site_identity, seat_identity |
| `agentmail/lib/security_lock_patterns.txt:22` | person_or_site_identity, seat_identity |
| `agentmail/lib/test_model_guard.py:47` | person_or_site_identity |
| `agentmail/lib/test_model_guard.py:66` | person_or_site_identity, private_project_reference, seat_identity |
| `agentmail/lib/test_model_guard.py:70` | person_or_site_identity, seat_identity |
| `agentmail/lib/test_model_guard.py:75` | person_or_site_identity, seat_identity |
| `agentmail/lib/test_model_guard.py:82` | person_or_site_identity, private_project_reference, seat_identity |
| `agentmail/lib/test_model_guard.py:83` | person_or_site_identity |
| `agentmail/lib/test_model_guard.py:227` | person_or_site_identity, private_project_reference, seat_identity |
| `agentmail/lib/test_model_guard.py:229` | person_or_site_identity |
| `agentmail/lib/test_model_guard.py:233` | person_or_site_identity |
| `agentmail/research/modelpick/catalogue_check.py:13` | private_project_reference |
| `agentmail/research/modelpick/catalogue_check_output.txt:5` | person_or_site_identity, seat_identity |
| `agentmail/research/modelpick/catalogue_check_output.txt:6` | person_or_site_identity, private_project_reference, seat_identity |

## Supplementary semantic review

Locations below use the incoming review snapshot's line numbers for corrected design passages and the current source line numbers elsewhere.
Design references in this section are remediation provenance: the cited title, task breadcrumbs, incident name and private roster excerpt were generalized in this round.
Scripts, fixtures, policy data and generated evidence still require their separately authorized owner.
The semantic pass inspected historical incident narratives, authorization comments, roster-derived fixture descriptions, policy provenance and branch/commit breadcrumbs across the public payload.
Generic policy guidance is not itself classified as private context.
No original values or descriptions are reproduced here.

| Location | Category |
| --- | --- |
| `agentmail/bin/agentmail-launch:140` | internal_research_task_reference |
| `agentmail/bin/agentmail-launch:142` | private_operational_context |
| `agentmail/bin/agentmail-launch:319` | private_operational_context |
| `agentmail/bin/agentmail-launch:333` | private_operational_context |
| `agentmail/bin/agentmail-launch:352` | private_operational_context |
| `agentmail/bin/agentmail-launch:417` | private_operational_context |
| `agentmail/bin/agentmail-launch:438` | private_operational_context |
| `agentmail/bin/agentmail-launch:586` | private_operational_context |
| `agentmail/bin/catalog-check:11` | private_operational_context |
| `agentmail/bin/catalog-check:4` | internal_research_task_reference |
| `agentmail/bin/codex-models:6` | private_operational_context |
| `agentmail/bin/fleet-guard:107` | private_operational_context |
| `agentmail/bin/fleet-guard:116` | private_operational_context |
| `agentmail/bin/fleet-guard:122` | private_operational_context |
| `agentmail/bin/fleet-guard:126` | private_operational_context |
| `agentmail/bin/fleet-guard:138` | private_operational_context |
| `agentmail/bin/fleet-guard:19` | private_operational_context |
| `agentmail/bin/fleet-guard:42` | private_operational_context |
| `agentmail/bin/fleet-guard:59` | private_operational_context |
| `agentmail/bin/fleet-usage:41` | private_operational_context |
| `agentmail/bin/fleet-watch.command:5` | private_operational_context |
| `agentmail/bin/whereami:110` | private_operational_context |
| `agentmail/bin/whereami:5` | private_operational_context |
| `agentmail/lib/model_guard.py:1` | internal_research_task_reference |
| `agentmail/lib/model_guard.py:3` | private_operational_context |
| `agentmail/lib/model_guard.py:30` | private_operational_context |
| `agentmail/lib/model_guard.py:61` | private_operational_context |
| `agentmail/lib/model_guard.py:62` | private_operational_context |
| `agentmail/lib/security_lock_patterns.txt:10` | private_operational_context |
| `agentmail/lib/security_lock_patterns.txt:17` | private_operational_context |
| `agentmail/lib/security_lock_patterns.txt:23` | private_operational_context |
| `agentmail/lib/test_model_guard.py:13` | internal_research_task_reference |
| `agentmail/lib/test_model_guard.py:232` | internal_research_task_reference |
| `agentmail/lib/test_model_guard.py:49` | internal_branch_commit_reference |
| `agentmail/lib/test_model_guard.py:5` | private_operational_context |
| `agentmail/lib/test_model_guard.py:58` | internal_research_task_reference |
| `agentmail/lib/test_model_guard.py:61` | private_operational_context |
| `agentmail/lib/test_model_guard.py:65` | private_operational_context |
| `agentmail/lib/test_model_guard.py:69` | verbatim_original_private_task_description |
| `agentmail/lib/test_model_guard.py:73` | verbatim_original_private_task_description |
| `agentmail/lib/test_model_guard.py:79` | private_operational_context |
| `agentmail/lib/test_model_guard.py:91` | internal_research_task_reference |
| `agentmail/research/modelpick/DESIGN.md:108` | private_operational_context |
| `agentmail/research/modelpick/DESIGN.md:12` | internal_research_task_reference |
| `agentmail/research/modelpick/DESIGN.md:13` | internal_branch_commit_reference |
| `agentmail/research/modelpick/DESIGN.md:192` | named_internal_incident |
| `agentmail/research/modelpick/DESIGN.md:2` | internal_research_task_reference |
| `agentmail/research/modelpick/DESIGN.md:233` | verbatim_original_private_task_description_prefix |
| `agentmail/research/modelpick/DESIGN.md:318` | private_operational_context |
| `agentmail/research/modelpick/phase2_demo.py:43` | internal_branch_commit_reference |

| `agentmail/OPERATIONAL_RULES.md:25` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:39` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:96` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:98` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:138` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:173` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:183` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:207` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:208` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:211` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:232` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:238` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:242` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:255` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:269` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:291` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:292` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:310` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:320` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:331` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:349` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:369` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:416` | private_operational_context |
| `agentmail/OPERATIONAL_RULES.md:429` | private_operational_context |
| `agentmail/research/modelpick/DESIGN.md:82` | private_operational_context |
| `agentmail/research/modelpick/DESIGN.md:165` | private_operational_context |
| `agentmail/research/modelpick/DESIGN.md:294` | private_operational_context |
| `agentmail/lib/test_model_guard.py:62` | private_operational_context |
| `agentmail/lib/test_model_guard.py:81` | private_operational_context |
| `agentmail/lib/test_model_guard.py:84` | private_operational_context |
| `agentmail/lib/test_model_guard.py:85` | private_operational_context |
| `agentmail/lib/test_model_guard.py:86` | private_operational_context |
| `agentmail/lib/test_model_guard.py:87` | private_operational_context |
| `agentmail/lib/test_model_guard.py:88` | private_operational_context |
| `agentmail/lib/test_model_guard.py:89` | private_operational_context |
| `agentmail/lib/test_model_guard.py:90` | private_operational_context |
| `docs/changes/iac-onboarding-review-fixes.md:40` | superseded_coverage_claim |
| `docs/changes/iac-onboarding-review-fixes.md:41` | superseded_coverage_claim |

## Intentional retained attribution and public source links

Legal attribution and the public toolkit source URL remain intact.
These locations matched the identity scan but are not private operational payload.

| Location | Category |
| --- | --- |
| `LICENSE:3` | legal_attribution |
| `README.md:240` | public_source_link |
| `agentmail/SETUP_PROMPT.md:59` | public_source_link |
| `agentmail/diagram/index.html:16` | public_source_link |
| `agentmail/diagram/index.html:41` | public_source_link |

## Coverage and remaining gate

The prior identifier scan inspected 133 tracked/nonignored files and found 92 category matches across 54 unique locations: 49 pending and five intentionally retained.
Those counts describe that earlier token scan only; supplementary semantic locations above are additional and may overlap its rows.
A semantic pass cannot prove absence of every private operational detail.
The full repository public-safety gate remains OPEN until the separately owned operational and generated-evidence locations are resolved.
No cloud service, external repository, deployment, terminal application, or fleet session was accessed.
