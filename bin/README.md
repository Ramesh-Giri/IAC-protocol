# Workspace setup commands

`iac-bootstrap` reads ignored `../projects.local.json`, or the safe `../projects.example.json` preview and clones or fast-forwards project checkouts inside the IAC root.
It never installs dependencies, configures accounts, deploys, or creates agent seats.
Run `python3 bin/test_iac_bootstrap.py` for its offline preservation checks.
