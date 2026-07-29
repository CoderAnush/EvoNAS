# GitHub Release Checklist (v0.7.0)

## Topics (suggested)

`automl` `neural-architecture-search` `particle-swarm-optimization` `pytorch` `reproducible-research` `python`

## Pre-release

- [ ] README badges show v0.7.0  
- [ ] LICENSE present  
- [ ] CONTRIBUTING present  
- [ ] Issue + PR templates present  
- [ ] CI workflow (optional follow-up)  

## Publish

1. Merge/commit freeze on `main`  
2. `git tag -a v0.7.0 -m "EvoNAS v0.7.0 — Phase 7 freeze / RC1"`  
3. `git push origin main --tags`  
4. Create GitHub Release: paste `docs/rc1/RELEASE_NOTES_RC1.md`  

## Post-release

- [ ] Verify `pip install` from tag works  
- [ ] Pin demo commands in README against tag  
- [ ] Open Phase 8 tracking issue
