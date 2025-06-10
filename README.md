# tablecensus

Defining ACS data pulls with data dictionaries, then the data work is automatic.


## Commands

`start`

To start working with table census you need to create a data dictionary that the tool will read to assemble your data pull. To create this table, use `tablecensus start`.

This will create a file in the working folder 'data_dictionary_<today's date>.xlsx.' This is the file that you'll use to define your datapull.

`assemble`

Once you've finished editing the data dictionary, you can run `tablecensus assemble <data dictionary filename>` and it will pull from the API and return a file 'report_<today's date>.xlsx'.

## How the data dictionary works

*Explanation to come but iykyk*

## Installation
1. You'll need to install git, if you haven't already [following the instructions for your operating system](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  - **For Windows users**, using this Git package is okay: https://git-scm.com/download/win 
2. Install the package manager `uv` [following these instructions](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1).
3. Then install tablecensus on your console with:
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

