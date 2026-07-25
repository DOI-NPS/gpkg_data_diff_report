# README

The files here are used to reconcile different versions of the SDE databases,
which have been exported to geopackage (.gpkg) files. There are scripts that
generate reports showing pairwise differences between the .gpkg files. There
are also scripts that can used to reconcile the differences and create a
definitive version of the database.

## Data diffing reports

### File descriptions

### Usage

Create a file called comparison_dict.py. It needs to include a nested dictionary
describing the geopackage comparisons to include. Use this template, with all the
comparisons to include in a single report:

```python
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

### Example run

## Reconciliation

### File descriptions

### Usage

### Example run