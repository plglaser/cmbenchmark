# Downloading and Preparing Datasets

Use `scripts/download_datasets.py` to download the supported public datasets, extract them, and copy the model files used by the benchmark profiles into `data/`.

```bash
.venv/bin/python scripts/download_datasets.py
```

The script uses only the requested model formats:

- EA ModelSet: `.archimate` files only
- ModelSet UML: XMI `.xmi` files only
- ModelSet Ecore: `.ecore` files only
- Atlantic Zoo: `.ecore` files only

Downloaded archives are cached in `downloads/`.

## Options

```bash
# List available dataset targets
.venv/bin/python scripts/download_datasets.py --list

# Download only one dataset target
.venv/bin/python scripts/download_datasets.py --only eamodelset
.venv/bin/python scripts/download_datasets.py --only modelset-uml
.venv/bin/python scripts/download_datasets.py --only modelset-ecore
.venv/bin/python scripts/download_datasets.py --only atlanticzoo

# Download multiple selected targets
.venv/bin/python scripts/download_datasets.py --only eamodelset --only atlanticzoo

# Re-download archives and replace selected output directories
.venv/bin/python scripts/download_datasets.py --force

# Custom output or archive cache location
.venv/bin/python scripts/download_datasets.py --data-dir /path/to/data
.venv/bin/python scripts/download_datasets.py --downloads-dir /path/to/downloads
```

Available `--only` values:

| Value | Description | Output directory |
| --- | --- | --- |
| `eamodelset` | EA ModelSet ArchiMate files only | `data/eamodelset/` |
| `modelset-uml` | ModelSet UML XMI files only | `data/modelset-uml/` |
| `modelset-ecore` | ModelSet Ecore files only | `data/modelset/` |
| `atlanticzoo` | Atlantic Zoo Ecore files | `data/atlanticzoo/` |

Prepared output layout:

```text
data/
├── eamodelset/
│   └── <model-id>.archimate
├── modelset-uml/
│   └── <model-id>.xmi
├── modelset/
│   └── <original-modelset-ecore-path>.ecore
└── atlanticzoo/
    └── <original-atlantic-zoo-path>.ecore
```

## EA ModelSet

Download link: [eamodelset.zip](https://github.com/me-big-tuwien-ac-at/EAModelSet/releases/download/v0.0.3/eamodelset.zip)

The script extracts `processed-models/*/model.archimate` and copies each file into `data/eamodelset/` as `<model-id>.archimate`, where `<model-id>` is the source model directory name.

JSON, XML, and CSV files from the archive are ignored.

Manual equivalent:

1. Download and extract `eamodelset.zip`.
2. Find `processed-models/*/model.archimate`.
3. Copy each file into `data/eamodelset/` as `<model-id>.archimate`.

## ModelSet UML

Download link: [modelset.zip](https://github.com/modelset/modelset-dataset/releases/download/v0.9.4/modelset.zip)

The script extracts `modelset/raw-data/repo-genmymodel-uml/data/*.xmi` and copies the files into `data/modelset-uml/` as flat `.xmi` files.

ModelSet UML JSON graph files are ignored.

Manual equivalent:

1. Download and extract `modelset.zip`.
2. Find `modelset/raw-data/repo-genmymodel-uml/data/*.xmi`.
3. Copy the `.xmi` files into `data/modelset-uml/`.

## ModelSet Ecore

Download link: [modelset.zip](https://github.com/modelset/modelset-dataset/releases/download/v0.9.4/modelset.zip)

The script extracts `modelset/raw-data/repo-ecore-all/data/**/*.ecore` and copies the files into `data/modelset/`, preserving the original nested path below the source `data/` directory.

ModelSet Ecore JSON graph files are ignored.

Manual equivalent:

1. Download and extract `modelset.zip`.
2. Find `modelset/raw-data/repo-ecore-all/data/**/*.ecore`.
3. Copy the `.ecore` files into `data/modelset/`, preserving their relative paths.

## Atlantic Zoo

Download link: [atlantic-zoo main branch ZIP](https://github.com/atlanmod/atlantic-zoo/archive/refs/heads/main.zip)

The script extracts `AtlantEcore/**/*.ecore` from the Atlantic Zoo repository archive and copies the files into `data/atlanticzoo/`, preserving the original nested path below `AtlantEcore/`.

Manual equivalent:

1. Download or clone `https://github.com/atlanmod/atlantic-zoo`.
2. Find `.ecore` files below `AtlantEcore/`.
3. Copy the `.ecore` files into `data/atlanticzoo/`, preserving their relative paths.
