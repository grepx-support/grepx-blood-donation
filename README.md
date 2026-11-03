# grepx-blood-donation

LifeFlow Blood Camp on the GrepX platform - and the workspace you run it from.

| Folder | What |
|---|---|
| `product-services/blood-donation/` | donation-service, donor-service (saved groups, import queue), `deployment.yaml` (how blood donation plugs into the generic services), `plugins/` (blood profile, eligibility, audiences, report figures), `catalog/` (templates, playbook, permissions, schedules) |
| `apps/blood-donation-bff/` | JSON API `/api/v1` + the original web site (`web/`) |
| `apps/web/` | the web UI shell (`products/blood-donation.json`, `modules/`) |
| `config/` | `common.yaml` (platform defaults), `projects/` (incl. the BFF `vocabulary:`), `services.ini` (what runs, ports) |
| `grepx.workspace.yaml` | the product, its deployment file, pinned platform / services / Nexus versions |
| `catalog/`, `docs/SERVICE_CATALOG.md` | generated service registry |

## Set up

```bash
# the other repos sit next to this one: ../grepx-platform ../grepx-services ../grepx-nexus-cpp
./workspace.sh clone          # or ./workspace.sh if they are already cloned - links platform/, scripts/, common-services/ …
scripts/infra.sh              # first time on a machine
scripts/setup.sh              # tooling + generated contracts + every service's .venv and database
scripts/run.sh start && scripts/run.sh seed
scripts/run.sh admin EMAIL PASSWORD "NAME" PHONE
```

Linked folders are git-ignored here; change platform or generic-service code in its own repo.
Moving from the old single repo: stop the services, copy `platform/nexus-server/bin/nexus_data.db` and `data/` across,
`scripts/run.sh migrate 001-generic-services`, `scripts/run.sh migrate 002-people-service`, then start and seed. (Windows: run in WSL - the workspace uses symlinks.)
