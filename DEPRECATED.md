# Retired

This repo held the first copy of the Cycle Demand dashboard. The app now lives
in the AM01 course fork, which is the one that gets deployed:

**https://github.com/Armandundar/am01-code-sep2026** — under `bikes_dashboard/`

`render.yaml` and `Procfile` were removed from here on 2026-09-09. Both declared
a service named `cycle-demand`, which is how a Render service ended up pointed
at this repo while its blueprint pointed at the fork: the deploy then failed with
`Root directory "bikes_dashboard" does not exist`, because that folder only
exists in the fork.

Nothing here is deployed. Treat it as an archive.
