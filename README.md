# tablecensus

Defining ACS data pulls with data dictionaries, then the data work is automatic.


## Commands

`start`
`assemble`


## Installation

1. If you haven't already, first install `uv` [following these instructions](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1).
2. Then install tablecensus on your console with:
```bash
uv tool install git+https://github.com/data-driven-detroit/tablecensus.git
```

### Mac Users

Users on MAC have to run an additional command to make sure the requests are sent correctly:

```
/Applications/Python\ 3.12/Install\ Certificates.command
```

Change the version if you're not running python 3.12 run ```python3 -V``` if you're not sure.

## Upgrade

Periodically you should check for updates on the tool:

```
uv tool upgrade tablecensus
```

Or if it's easier you can update all your uv-installed tools.

```
uv tool update --all
```

