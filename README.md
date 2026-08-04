# README

These files are used to generate an HTML report that shows the pairwise differences between geopackage (.gpkg) files. The report lists differences in layers, table columns, and rows (i.e., inserted, deleted, and updated rows). Multiple pairwise comparisons can be included in the same report.

In each pairwise comparison of the report, the original version is called "A" and the modified version is called "B." Inserted and deleted rows are relative to the original or A version. Therefore, rows that are present only in A will be listed under the deleted rows, and rows present only in B are under the inserted rows.

## File descriptions

- custom_diff_functions.py: Functions called by the report generation script. Includes functions that read geopackages into dictionaries and find differences between the datasets.
- report_specifications.py: Not included in the repo, but a template for the file is in the usage section below. This file specifies the information that should be included in the HTML report.
- data_difference_report.py: This script generates the HTML report and calls custom_diff_functions.py and report_specifications.py.

## Usage

Create a file in this folder called report_specifications.py. It needs to specify the (1) a tree in Newick format that describes the relationships between each version of the database (see note on Newick format below); (2) a file path for the HTML output; and (3) a nested dictionary describing the geopackage comparisons to include. Use this template:

```python
newick_tree = '((A,(B,C)), (D,E));'
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

---

**Newick format**

Newick format is typically used to represent phylogenetic trees, but it is used here to represent similar relationships between geopackage versions. Each group is surrounded by parentheses, and groups can be nested within one another. So "(A,B)" is one group and "(C,D)" is another, which could be assembled into the tree "((A,B),(C,D));". E can be added, making the tree "(((A,B),(C,D)),E);". In the five-tip tree, the first four letters make a larger group that doesn't include E. The tree would be visualized as:

              +---A
          +---|
          |   +---B
      +---| 
      |   |   +---C
    __|   +---|
      |       +---D
      |
      +-----------E

Newick trees require outer parentheses that surround the entire tree, along with a semicolon at the end. There are browser, command line, and desktop GUI tools that will visualize Newick format strings. These tools can be used to check the tree structure before generating the report.