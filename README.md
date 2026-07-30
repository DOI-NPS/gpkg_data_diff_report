# README

These files are used to generate an HTML report that shows the pairwise differences between geopackage (.gpkg) files. The report lists differences in layers, table columns, and rows (i.e., inserted, deleted, and updated rows). Multiple pairwise comparisons can be included in the same report.

## File descriptions

- custom_diff_functions.py: Functions called by the report generation script. Includes functions that read geopackages into dictionaries and find differences between the datasets.
- report_specifications.py: Not included in the repo, but a template for the file is below, in the usage section. This file specifies a file path for the generated report and a list of comparisons to include.
- data_difference_report.py: This script generates the HTML report and calls custom_diff_functions.py and report_specifications.py.

## Usage

Create a file called report_specifications.py. It needs to specify the file path for the HTML output. It also needs to include a nested dictionary describing the geopackage comparisons to include. Use this template:

```python
out_html_name = 'path/to/report_file.html'

comparisons = {
    1:{
      'name': 'gpkg A to gpkg B',
      'original': r'path/to/version_A.gpkg',
      'changed': r'path/to/version_B.gpkg'
      },
  
    2:{
      'name': 'gpkg A to gpkg C',
      'original': r'path/to/version_A.gpkg',
      'changed': r'path/to/version_C.gpkg'
      },
    
    3:{
      'name': 'gpkg D to gpkg E',
      'original': r'path/to/version_D.gpkg',
      'changed': r'path/to/version_E.gpkg'
      }
}
```

Then run the report generation script:

```python
python data_difference_report.py
```
In each pairwise comparison of the report, the original version is called "A" and the modified version is called "B." Inserted and deleted rows are relative to the original or A version. Therefore, rows that are present only in A will be listed under the deleted rows, and rows present only in B are under the inserted rows.