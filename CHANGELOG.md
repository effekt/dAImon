# Changelog

## 0.1.0 (2026-11-18)


### ⚠ BREAKING CHANGES

* remove the env-bridge Slack app ([#94](https://github.com/effekt/dAImon/issues/94))

### Features

* add Codex capacity fallback and Slack support ([#65](https://github.com/effekt/dAImon/issues/65)) ([a170af4](https://github.com/effekt/dAImon/commit/a170af472eb2b63e254a330ea8f4735a01729945))
* **backend:** add codex backend (one-shot `codex exec`) ([#41](https://github.com/effekt/dAImon/issues/41)) ([43ac206](https://github.com/effekt/dAImon/commit/43ac206b8eae1e3e7b41a3c4fce6a3e4b1a1174e))
* **catalog:** daemons become a catalog you install from ([#118](https://github.com/effekt/dAImon/issues/118)) ([f08c34f](https://github.com/effekt/dAImon/commit/f08c34f8d633c59c6223880931cdd82f5a8c0c82))
* **catalog:** eject daemons to edit, and see upstream changes ([#119](https://github.com/effekt/dAImon/issues/119)) ([842c099](https://github.com/effekt/dAImon/commit/842c099e9d49846ae087e8c24a6cd3eb1c18afce))
* **catalog:** fork a daemon under a new name with `daimon eject --as` ([#120](https://github.com/effekt/dAImon/issues/120)) ([c629b61](https://github.com/effekt/dAImon/commit/c629b6147db3e6a0766f318812366ae578492b76))
* command scaffolder + scheduled-command daemon ([#64](https://github.com/effekt/dAImon/issues/64)) ([ac21479](https://github.com/effekt/dAImon/commit/ac214798cd39eebf2a9780da3c1772446333a5c8))
* **config:** keep personal settings in ~/.config/daimon, migrating legacy *.local.toml ([#117](https://github.com/effekt/dAImon/issues/117)) ([184a852](https://github.com/effekt/dAImon/commit/184a85266ed5bfdb55e805a507a3cf4785c938d7))
* **config:** move the personal dir from ~/.config/daimon to ~/.daimon ([#121](https://github.com/effekt/dAImon/issues/121)) ([33520d9](https://github.com/effekt/dAImon/commit/33520d9415886e0bdfc153603f53276a9b21605d))
* **daemons:** add datadog-log-reviewer daemon + datadog source profile ([#47](https://github.com/effekt/dAImon/issues/47)) ([b5de106](https://github.com/effekt/dAImon/commit/b5de106eefd6415f6d3a1afff160bbc7cc5f044e))
* **daemons:** add risk-tiered dependency-reviewer daemon ([#46](https://github.com/effekt/dAImon/issues/46)) ([2cb3235](https://github.com/effekt/dAImon/commit/2cb32351b926e661c3ecb4a12c7e8e343eb28d10))
* **daemons:** add slack-standup — daily standup poster via Slack MCP ([#63](https://github.com/effekt/dAImon/issues/63)) ([6afc54f](https://github.com/effekt/dAImon/commit/6afc54f7386ca43b5e350b8e0bd0fe1f22c5201b))
* **daemons:** audit sources + add reply-to-story-comments ([b6e3871](https://github.com/effekt/dAImon/commit/b6e387132f6bc613048d8413dcb67ba17e98dc32))
* **daemons:** enable Codex second opinion on review-prs and story-reviewer ([#42](https://github.com/effekt/dAImon/issues/42)) ([871befe](https://github.com/effekt/dAImon/commit/871befeb183924250dddbcf4db34f18bdaf33448))
* **daemons:** private daemons via a .local folder suffix ([#86](https://github.com/effekt/dAImon/issues/86)) ([8e50d32](https://github.com/effekt/dAImon/commit/8e50d32eea6946e1d74cadd8aa5a0fabc833d88a))
* **daemons:** richer, configurable review/reply output ([#16](https://github.com/effekt/dAImon/issues/16)) ([d8e8c82](https://github.com/effekt/dAImon/commit/d8e8c82094ee46097f07c668d2ecd59a9392546e))
* dAImon — scheduled autonomous agent daemon pipeline ([daf5230](https://github.com/effekt/dAImon/commit/daf52301be6f2268beaf4a087ecf5b0b9ac658ac))
* daimon init, first-run DX, and OSS scaffolding ([#17](https://github.com/effekt/dAImon/issues/17)) ([704a69e](https://github.com/effekt/dAImon/commit/704a69e6a7a1b1165ec7879ab5caf036845a8544))
* **docs:** keep git-excluded daemons out of the committed index ([#61](https://github.com/effekt/dAImon/issues/61)) ([5619605](https://github.com/effekt/dAImon/commit/5619605744f225b201566a1e68871f0fe7838507))
* **doctor:** check codex CLI/auth and warn on untrusted working_dir ([#43](https://github.com/effekt/dAImon/issues/43)) ([5a3ae44](https://github.com/effekt/dAImon/commit/5a3ae440578a0a6ffdc9010d5f1160c17a01d787))
* github source profile — shared gate helpers + bats ([#14](https://github.com/effekt/dAImon/issues/14)) ([b8a7368](https://github.com/effekt/dAImon/commit/b8a736848e0010b3fbf151cfc5651f8d9a6a13ab))
* JSON Schema for daemon.toml (editor validation) ([#11](https://github.com/effekt/dAImon/issues/11)) ([eca9f83](https://github.com/effekt/dAImon/commit/eca9f8389cf4ecee560e2b087992bf2393f08f8c))
* let daimon init select which daemons to run ([#18](https://github.com/effekt/dAImon/issues/18)) ([c0a6914](https://github.com/effekt/dAImon/commit/c0a691452f151a48fcc5cffeab3e4956697538aa))
* **logging:** record what each run did, not just that it ran ([#102](https://github.com/effekt/dAImon/issues/102)) ([8fa98e9](https://github.com/effekt/dAImon/commit/8fa98e9a57062093efc2a4a24ad613ee72e8e8a7))
* **mcp:** opt-in Codex MCP for daemon sessions ([#40](https://github.com/effekt/dAImon/issues/40)) ([2875932](https://github.com/effekt/dAImon/commit/2875932e1e93176ee2f6262573f5f3e0a8708b7b))
* multi-source profiles + story-aware PR review ([#13](https://github.com/effekt/dAImon/issues/13)) ([93447b8](https://github.com/effekt/dAImon/commit/93447b85abf10f65d15c5106677bdaae892e740c))
* **packs:** load daemons, team overrides and runbooks from folders outside the repo ([#111](https://github.com/effekt/dAImon/issues/111)) ([a2de9e5](https://github.com/effekt/dAImon/commit/a2de9e5c8a8bcccf6ba6a16d44cc078d925d0b42))
* pr-manager daemon — shepherd open PRs to merge ([#3](https://github.com/effekt/dAImon/issues/3)) ([6a49021](https://github.com/effekt/dAImon/commit/6a49021f98b71f8c056afd717c6c53b5582b0718))
* **pr-manager:** draft self-promotion + configurable reviewers ([#4](https://github.com/effekt/dAImon/issues/4)) ([c7f69ed](https://github.com/effekt/dAImon/commit/c7f69edb5ee38ee63144cd8731c96b19d2934357))
* **pr-manager:** handle review findings before merging, resuming the session that wrote the PR ([#107](https://github.com/effekt/dAImon/issues/107)) ([aed2e94](https://github.com/effekt/dAImon/commit/aed2e94b6b2526f2400b92b5d15ce306bac1bc72))
* **pr-manager:** optional unattended auto-merge ([#5](https://github.com/effekt/dAImon/issues/5)) ([dc336fe](https://github.com/effekt/dAImon/commit/dc336fefa03a767084d4afbb4fde6296669ad889))
* read-only vs read-write source modes (reference split) ([#15](https://github.com/effekt/dAImon/issues/15)) ([f4e50c7](https://github.com/effekt/dAImon/commit/f4e50c7eda7be82d398f33ad8a97c441ba0ead55))
* **review-prs:** announce review pickup ([#67](https://github.com/effekt/dAImon/issues/67)) ([7f5bd84](https://github.com/effekt/dAImon/commit/7f5bd842cc7198f30c8a2d8a2861c3197051cd63))
* **review:** risk-gated review decisions + reply-driven re-review ([#7](https://github.com/effekt/dAImon/issues/7)) ([bbae133](https://github.com/effekt/dAImon/commit/bbae133f976bd8976dd31ec4f9a31664f97fe802))
* **roles:** run a daemon on one machine only ([#108](https://github.com/effekt/dAImon/issues/108)) ([a07e4d9](https://github.com/effekt/dAImon/commit/a07e4d94cb73acca7addb1a1b6e8a890149f8fea))
* **scaffold:** daimon scaffold writes an inert daemon skeleton, in dAImon or a pack ([#114](https://github.com/effekt/dAImon/issues/114)) ([491be0f](https://github.com/effekt/dAImon/commit/491be0fe5c51fcec487fc96f1905a4092d214c64))
* **shortcut,scope:** epic exclusion + an allowed-paths scope guard ([#60](https://github.com/effekt/dAImon/issues/60)) ([67b888c](https://github.com/effekt/dAImon/commit/67b888c6a0951fa96e58bf95362d4c2f8156282a))
* **shortcut:** a dropdown field can replace the marker labels; rank by a priority field ([#99](https://github.com/effekt/dAImon/issues/99)) ([ef71e08](https://github.com/effekt/dAImon/commit/ef71e08bb28d21e77985b623fcc36b8fd48f50c1))
* **shortcut:** exclude_labels keeps labelled stories out of every daemon ([#97](https://github.com/effekt/dAImon/issues/97)) ([5afbd99](https://github.com/effekt/dAImon/commit/5afbd99b9d054fc9acd6681b79276397c3f5fabc))
* **shortcut:** exclude_objectives keeps whole objectives out of every daemon ([#90](https://github.com/effekt/dAImon/issues/90)) ([3ce2fd6](https://github.com/effekt/dAImon/commit/3ce2fd6dbcecf800878f0a385c3c4cf323044375))
* **shortcut:** mirror assessments to a status field; reviewer unblocks reversible choices and splits multi-PR work ([#98](https://github.com/effekt/dAImon/issues/98)) ([884786b](https://github.com/effekt/dAImon/commit/884786b6ed1edfa65fb78b1a8ab8735ebbb18070))
* **shortcut:** opt epics back in out of an excluded objective ([#105](https://github.com/effekt/dAImon/issues/105)) ([881413c](https://github.com/effekt/dAImon/commit/881413cd728e11d82eea529fecf906eddb287084))
* **shortcut:** owner-only scope, not-started review intake, staleness checks ([#89](https://github.com/effekt/dAImon/issues/89)) ([bcf293c](https://github.com/effekt/dAImon/commit/bcf293cdbe13dcada70f3b98e07da24ce3fb8382))
* **shortcut:** priority_requesters puts chosen requesters' stories first ([#91](https://github.com/effekt/dAImon/issues/91)) ([ddd764d](https://github.com/effekt/dAImon/commit/ddd764d37a8abb757df26177d002e2a2eeb6672b))
* **shortcut:** support epic_id on story creation ([#50](https://github.com/effekt/dAImon/issues/50)) ([17017d0](https://github.com/effekt/dAImon/commit/17017d032f4ef7723a09e143a8a3a04f25b35e12))
* **skills:** shared conventions include for comment-posting daemons ([#12](https://github.com/effekt/dAImon/issues/12)) ([fdc7eca](https://github.com/effekt/dAImon/commit/fdc7eca51d3bdd8c00b720bb091b66ff38493819))
* **state:** route daemon state through a daimon state get/set utility ([#53](https://github.com/effekt/dAImon/issues/53)) ([82a0942](https://github.com/effekt/dAImon/commit/82a094284b2bff60f1b1f212e80936329e4b7e15))
* **status:** report daemon status to an optional [status].command ([#109](https://github.com/effekt/dAImon/issues/109)) ([07cbbc8](https://github.com/effekt/dAImon/commit/07cbbc80961e84c1b15b4b439afc8104ad426215))
* **story-reviewer:** an assigned story is approved; ask only when a real blocker applies ([#103](https://github.com/effekt/dAImon/issues/103)) ([76d7201](https://github.com/effekt/dAImon/commit/76d7201e8defeb5bb6b9608d7743a4c5fcd658ff))
* **story-reviewer:** close provably obsolete stories into a configured state ([#101](https://github.com/effekt/dAImon/issues/101)) ([ac784e9](https://github.com/effekt/dAImon/commit/ac784e929f53e66a8b8cc36e953cf1a8bde044ac))
* **tui:** audit — newest-first log tail, complete manage menu, drop dead source field ([#20](https://github.com/effekt/dAImon/issues/20)) ([46caf24](https://github.com/effekt/dAImon/commit/46caf24ed859e0c46c69e68b3e47b8791cb70e84))
* **tui:** batch refresh queries; safer daemon duplication ([#21](https://github.com/effekt/dAImon/issues/21)) ([4418dc6](https://github.com/effekt/dAImon/commit/4418dc697a0c8b34c7951d10a70768e70d130ddc))
* **tui:** glyph-based status with a legend (no colour-only state) ([#22](https://github.com/effekt/dAImon/issues/22)) ([4972c56](https://github.com/effekt/dAImon/commit/4972c56e96eeee25c7b4d1d20c4ce3610be3c6c8))
* **tui:** separate daemon inputs from profile fields in config editor ([#19](https://github.com/effekt/dAImon/issues/19)) ([7a24390](https://github.com/effekt/dAImon/commit/7a243907e22ef277ac0b383051a31ac39f114a46))
* **update:** opt-in self-update, and per-daemon doctor checks ([#115](https://github.com/effekt/dAImon/issues/115)) ([2dbf9bc](https://github.com/effekt/dAImon/commit/2dbf9bc89ba21c9b07b6a7377dc041c56af821bf))
* **work-queue:** open_as_draft input to open PRs ready for review ([#88](https://github.com/effekt/dAImon/issues/88)) ([b6893b8](https://github.com/effekt/dAImon/commit/b6893b8c1e13b0fbd87bc6e87128d5ef44c9f41e))
* **work-queue:** pick stalled claims back up; never stall on a permission prompt ([#95](https://github.com/effekt/dAImon/issues/95)) ([0cd2661](https://github.com/effekt/dAImon/commit/0cd2661298710f874925959e9bf2521ce600a504))
* **work-queue:** several stories per run, and remove finished worktrees ([#104](https://github.com/effekt/dAImon/issues/104)) ([99cfb75](https://github.com/effekt/dAImon/commit/99cfb756beb148bdedce636bc633ec2baf501dc8))


### Bug Fixes

* **budget:** exempt daemons no longer consume the shared hourly pool ([#93](https://github.com/effekt/dAImon/issues/93)) ([d9bfddf](https://github.com/effekt/dAImon/commit/d9bfddf959c7110aba02a125811d9747892377a3))
* **catalog:** daimon remove unloads a leftover job of a daemon not installed ([#125](https://github.com/effekt/dAImon/issues/125)) ([dbaff62](https://github.com/effekt/dAImon/commit/dbaff6228ebe1696ca541460d38d9b6df85961f3))
* **config:** keep quotes, backslashes and newlines when writing TOML; neutral examples ([#112](https://github.com/effekt/dAImon/issues/112)) ([e6e884f](https://github.com/effekt/dAImon/commit/e6e884fa86fd770993fc512a6a31d1c8d2734ec8))
* **daemons:** stop agents leaking state files into the target repo ([#52](https://github.com/effekt/dAImon/issues/52)) ([cc87a59](https://github.com/effekt/dAImon/commit/cc87a5922ad7818b11b132022210bdc2527d0952))
* **datadog-log-reviewer:** adopt an open story instead of filing a duplicate ([#110](https://github.com/effekt/dAImon/issues/110)) ([efc75e6](https://github.com/effekt/dAImon/commit/efc75e62627ae5a839d93776ecfac9b08a80d211))
* full verbosity in reply daemons names files/changes ([#28](https://github.com/effekt/dAImon/issues/28)) ([0d60b05](https://github.com/effekt/dAImon/commit/0d60b05deca6e0c8656c24e95c6244aadd706b1c))
* **install:** make install registers no daemon ([#116](https://github.com/effekt/dAImon/issues/116)) ([61abf63](https://github.com/effekt/dAImon/commit/61abf63fc0b4cca2072df70a6dee7e82cc5d876a))
* **launch:** a child `claude -p` can no longer end the daemon's run ([#96](https://github.com/effekt/dAImon/issues/96)) ([afb6894](https://github.com/effekt/dAImon/commit/afb68943f9f4fea979f1f8b51c383d619cb05918))
* **pr-manager:** repair conflicting or red drafts ([#87](https://github.com/effekt/dAImon/issues/87)) ([9711bb8](https://github.com/effekt/dAImon/commit/9711bb86c10d2d1bc955cef5d02818e003b61478))
* **review-prs:** make discovery gate state-aware ([#6](https://github.com/effekt/dAImon/issues/6)) ([a15d658](https://github.com/effekt/dAImon/commit/a15d658c1cd9ef9adedcdb783d47db65d7ea2135))
* **runtime:** enforce hourly budget gate and make watchdog backend-agnostic ([#44](https://github.com/effekt/dAImon/issues/44)) ([ad6736b](https://github.com/effekt/dAImon/commit/ad6736be7037a289a2df3080ed7dbcda9c9cb593))
* scope work-queue to the owner's own stories ([ac9deda](https://github.com/effekt/dAImon/commit/ac9dedac2ab7fa739a7447995913ad9f2624f12d))
* **setup:** daemon setup initialization ([#51](https://github.com/effekt/dAImon/issues/51)) ([7186fd3](https://github.com/effekt/dAImon/commit/7186fd35bd67994241cae8755e717bc4f9f0b742))
* **shortcut:** a cleared marker means re-review, never an opt-out ([#100](https://github.com/effekt/dAImon/issues/100)) ([dc43ad1](https://github.com/effekt/dAImon/commit/dc43ad106c64e2bb6bf58cb2d00965250bf21124))
* **story-reviewer, work-queue:** wider triage intake, unblock the work-queue gate ([#85](https://github.com/effekt/dAImon/issues/85)) ([2eb50b0](https://github.com/effekt/dAImon/commit/2eb50b08d9fcd1ba5cfe7dcaab91d09644dd07df))
* **story-reviewer:** unambiguous wording for the not-started intake switch ([#92](https://github.com/effekt/dAImon/issues/92)) ([512515e](https://github.com/effekt/dAImon/commit/512515e0f524f54ee38d5be91925c2ce489ceaa7))
* **sync,watchdog:** reload changed launchd jobs; reap finished sessions whose launcher died ([#106](https://github.com/effekt/dAImon/issues/106)) ([0eea797](https://github.com/effekt/dAImon/commit/0eea7973e1a93f46e87d31275ea981b93c75a8b8))
* **tui:** duplicate a catalog daemon through daimon eject --as ([#124](https://github.com/effekt/dAImon/issues/124)) ([4f86573](https://github.com/effekt/dAImon/commit/4f86573cb96dc06a7d9168526c48a24616761e16))


### Performance Improvements

* memoize discover() + single-shot daemon-env (kill per-run process storm) ([#10](https://github.com/effekt/dAImon/issues/10)) ([e1571d1](https://github.com/effekt/dAImon/commit/e1571d119254fee3c2920f87dd49afdf017cc916))
* **review-prs:** poll every 10 seconds ([#68](https://github.com/effekt/dAImon/issues/68)) ([cd845f5](https://github.com/effekt/dAImon/commit/cd845f5d7f04b5dd850663251a0697468a5fe498))


### Documentation

* add a migration guide for the catalog and ~/.daimon changes ([#122](https://github.com/effekt/dAImon/issues/122)) ([d89405f](https://github.com/effekt/dAImon/commit/d89405ffa62ca90e95522f0c85665acac6563a38))
* add a TUI screenshot to the README ([#26](https://github.com/effekt/dAImon/issues/26)) ([fb98db8](https://github.com/effekt/dAImon/commit/fb98db86e0ab645bb190f36d03955c6ca675bd45))
* add AGENTS.md + committed permissions-only .claude/settings.json ([#9](https://github.com/effekt/dAImon/issues/9)) ([509504d](https://github.com/effekt/dAImon/commit/509504d02dcb1532179259087dc2738874d4630c))
* add writing-a-source how-to for source profiles ([#49](https://github.com/effekt/dAImon/issues/49)) ([2803a8a](https://github.com/effekt/dAImon/commit/2803a8ab9b98fa6c3fab115dc07ad338c72ffa73))
* correct main protection description (no required reviews) ([#36](https://github.com/effekt/dAImon/issues/36)) ([8cd5f56](https://github.com/effekt/dAImon/commit/8cd5f560d1b4ffca599e4648a591d4c573f47c8c))
* fix branch-protection command and document release-PR merges ([#35](https://github.com/effekt/dAImon/issues/35)) ([57974d6](https://github.com/effekt/dAImon/commit/57974d6982baaaf03996bd36d85e671373861cef))
* generate per-daemon READMEs + index, enforced ([#27](https://github.com/effekt/dAImon/issues/27)) ([e9d63fd](https://github.com/effekt/dAImon/commit/e9d63fd3c1a91b5f35b00c4c097b351bc36225cb))
* lead README with purpose; fill CONTRIBUTING gaps ([#29](https://github.com/effekt/dAImon/issues/29)) ([e85b23b](https://github.com/effekt/dAImon/commit/e85b23bf15d25e56e6bf89a2d0eb1d7ef4f0c477))
* **readme:** install --load schedules every daemon that isn't disabled ([#113](https://github.com/effekt/dAImon/issues/113)) ([4c557cc](https://github.com/effekt/dAImon/commit/4c557cc5dd508629f22c982e1d60183461fd729e))


### Miscellaneous Chores

* remove the env-bridge Slack app ([#94](https://github.com/effekt/dAImon/issues/94)) ([cdbba46](https://github.com/effekt/dAImon/commit/cdbba460224f3fa160427fece992f609276d8b3d))

## Changelog

All notable changes are recorded here. Entries below are generated from
[Conventional Commits](https://www.conventionalcommits.org/) by
[release-please](https://github.com/googleapis/release-please); the version follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).
