# tablecensus

## Define American Community Survey data pulls with spreadsheet-based data dictionaries, then the data work is automatic.

Pull American Community Survey (ACS) data from the Census Bureau by filling out an Excel spreadsheet. No API calls, no data wrangling—just define what you want and tablecensus does the rest.

## Commands

`start`

To start working with table census you need to create a data dictionary that the tool will read to assemble your data pull. To create this table, use `tablecensus start`.

This will create a file in the working folder `data_dictionary_<today's date>.xlsx.` This is the file that you'll use to define your datapull.

`assemble`

Once you've finished editing the data dictionary, you can run `tablecensus assemble <data dictionary filename>` and it will pull from the API and return a file `report_<today's date>.xlsx`.

### Short geoids: 

`assemble` has the flag `-s` or `--short-geoids` which will return shorter geoids to interoperate with the datasets that use them. For example, the `GEO_ID` field returns a 21-character normally, but some tools like [censusreporter](censusreporter.org) and [IPUMS NHGIS](https://www.nhgis.org/) use shorter geoids.


## How the data dictionary works

Define variables and select geographies in the `data_dictionary_<date>.xlsx` file created by the command `tablecensus start`.
Then you can run `tablecensus assemble <this filename>.xlsx` to turn these definitions into a report.

Variables: give each variable a name and use ACS codes to write out the calculation for that name. Basic arithmetic works 

Years: choose which year(s) you'd like the data pulled for and which release (i.e. 1-year, 5-year)

Geographies: select the geographies that you'd like to pull the data for, and fill in the correct geoid components. '*' will select all geographies that have the parent components, following the ACS API matching rules.

## Available Releases, Variable Library, and Geography Library tabs are available as references to aid you in filling in the other tabs.

The data dictionary is an Excel file with several sheets that define your data pull:

**Variables**: Define what census variables you want and any calculations
- `name`: What you want to call the variable in your output
- `calculation`: Either a single census variable (like `B01001001`) or a calculation (like `B17001002 / B17001001` for poverty rate)

**Years**: Specify which ACS survey years you want
- `year`: The survey year (e.g., 2018, 2019, 2023)
- `release`: The ACS release type (`acs1`, `acs3`, or `acs5`)

**Geographies**: Choose what geographic areas to include
- Fill in the appropriate columns for the geography levels you want
- Each row represents a different geography combination
- Examples: state `26` for Michigan, or county `163` within state `26` for Wayne County

The template includes reference sheets with common variables and geography examples to copy from.

## Features

- **Simple interface**: Define data pulls in Excel instead of writing API calls
- **Custom calculations**: Create new variables using census data (percentages, ratios, etc.)
- **Multi-geography support**: Pull data for states, counties, tracts, block groups, and more
- **Multi-year data**: Combine data across different ACS survey years
- **Optimized requests**: Automatically batches API calls for efficiency
- **Multiple output formats**: Export to Excel, CSV, or Parquet
- **Professional formatting**: Excel outputs include styling and formatting

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

## Examples

**Basic workflow:**
```bash
# Create a new data dictionary template
tablecensus start

# Edit the generated Excel file to define your variables, years, and geographies
# Then assemble your data
tablecensus assemble data_dictionary_2025-01-21.xlsx
```

**Common use cases:**
- Pull poverty rates for all counties in Michigan for 2018-2023
- Get demographic data for specific census tracts
- Compare housing characteristics across multiple metropolitan areas
- Create custom indicators by combining multiple census variables

