# Visualization Tool for Jupyter Notebooks based on Abstract Syntax Analysis
This is the implementation of the thesis with the title "Exploring Jupyter Notebooks by Visualizing Data Flow Paths from Abstract Syntax Trees." The visualization is the output and is based on abstract syntax trees of the notebook and its code. It allows users to understand code faster through data flow paths and control flow paths in the visualization.
## Requirements
The following external libraries are required to use the visualization tool:
 - PyGraphviz
 - nbformat
 - squarify
 - alive_progress 1.0
 - Beautiful Soup
 - requests-html

Python scripts were tested and executed using Python 3.10.6. Notebooks to be analyzed should be put in the ``notebooks`` folder, whereas the scripts should be placed in ``main``. The project is structured as follows:
```
jupyter_notebook_browsing
├── main
│   ├── extract_cfg.py
│   ├── extract_dfg.py
│   ├── process_kernels.py
│   └── render_html.py
├── notebooks
│   └── <Paste .ipynb-file in here>
├── output
│   └── <Output files from process_kernels.py are put in here>
└── resources
    └── color.csv
```
## Usage
 1. Paste the notebook to be taken into account for the analysis into the ``notebook`` folder.
 2. Run ``process_kernels.py`` and select the desired notebook
 3. After the visualization is computed, the visualization can be found within the ``output`` folder.
 4. Repeat with 1. for additional visualizations of notebooks.