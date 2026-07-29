# README

The files here are used to reconcile different versions of the SDE databases, which have been exported to geopackage (.gpkg) files. There are scripts that generate reports showing pairwise differences between the .gpkg files. There are also scripts that can used to reconcile the differences and create a definitive version of the database.

## Data diffing reports

These files are used to generate an HTML report that shows the pairwise differences between geopackages. The report includes differences in layers, table columns, and rows (i.e., inserted, deleted, and updated rows). Multiple pairwise comparisons can be put in the same report.

### File descriptions

- custom_diff_functions.py: Functions called by the report generation script. Includes functions that read geopackages into dictionaries and find differences between the datasets.
- report_specifications.py: Not included in the repo, but a template for the file is below, in the usage section. This file specifies a file path for the generated report and a list of comparisons to include.
- SDE_reconciliation_reports.py: This script generates the HTML report and calls custom_diff_functions.py and report_specifications.py.

### Usage

Create a file called report_specifications.py. Specify the file path for the HTML output. It also needs to include a nested dictionary describing the geopackage comparisons to include. Use this template:

```python
out_html_name = 'path/to/report_file.html'

comparisons = {
    1:{
      'name': 'gpkg A to gpkg B',
      'original': r'path/to/A.gpkg',
      'changed': r'path/to/B.gpkg'
      },
  
    2:{
      'name': 'gpkg A to gpkg C',
      'original': r'path/to/A.gpkg',
      'changed': r'path/to/C.gpkg'
      },
    
    3:{
      'name': 'gpkg D to gpkg E',
      'original': r'path/to/D.gpkg',
      'changed': r'path/to/E.gpkg'
      }
}
```

Then run the report generation script.

```python
python SDE_reconciliation_reports.py
```

## Data syncing

### File descriptions

### Usage
