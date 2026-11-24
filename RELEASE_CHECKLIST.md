# Beta release checklist

Use this before pushing `v1.0.0-beta.1`.

## Repository hygiene

- [ ] Check `git status` and review every changed file.
- [ ] Confirm `.env` is ignored.
- [ ] Confirm no passwords, API keys or database connection secrets are staged.
- [ ] Confirm no PostgreSQL dumps or local database files are staged.
- [ ] Confirm no voice recordings or speaker profile data are staged.
- [ ] Confirm downloaded model files are handled intentionally and their licences/redistribution terms are understood.
- [ ] Confirm `.venv`, caches and build artefacts are ignored.

## Validation

- [ ] Activate the intended virtual environment.
- [ ] Run the test suite.
- [ ] Start PostgreSQL and confirm the app can connect.
- [ ] Start Ollama and confirm the configured model is available.
- [ ] Launch Tuna and test a conversation.
- [ ] Restart Tuna and check conversation restoration.
- [ ] Check memory retrieval and explicit memory commands.
- [ ] Check the UI can enter and leave its main states without freezing.
- [ ] Mark voice as experimental until enrollment and verification tests pass.

## Git release

- [ ] Review README, CHANGELOG and ROADMAP.
- [ ] Commit the beta milestone.
- [ ] Create the annotated tag `v1.0.0-beta.1`.
- [ ] Push the branch and tag.

Suggested commands, after reviewing the staged changes:

```bash
git status
git diff
git diff --cached
git add README.md CHANGELOG.md ROADMAP.md RELEASE_NOTES_v1.0.0-beta.1.md CONTRIBUTING.md RELEASE_CHECKLIST.md
git commit -m "docs: prepare v1.0.0-beta.1 release"
git tag -a v1.0.0-beta.1 -m "Tuna v1.0.0-beta.1"
git push origin HEAD
git push origin v1.0.0-beta.1
```

Do not blindly copy the commands if your branch or staged changes differ. Review the complete diff first.
