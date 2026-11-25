# Contributing

Keep the brain/provider independent from the desktop UI. Voice services must run off the Qt UI thread. Never commit `.env`, audio recordings, speaker profiles or model weights. Add tests for state transitions and keep existing PostgreSQL data compatible unless a separately reviewed migration is supplied.
