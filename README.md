# HyperGraphRAG

## Dependence
```bash
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag
pip install torch==2.3.0
pip install -r requirements.txt
```

## Dataset
The dataset used in HyperGraphRAG can be downloaded from [TommyChien/UltraDomain](https://huggingface.co/datasets/TommyChien/UltraDomain). to `datasets/ultradomain/agriculture[cs,legal,mix].json`.

## Step-0 Extract Unique Contexts
```bash
python Step_0.py
```

## Step-1 Insert Contexts
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
python Step_1.py
```

## Step-2 Generate Queries
We extract tokens from the first and the second half of each context in the dataset, then combine them as dataset descriptions to generate queries.
```bash
python Step_2.py
```

## Step-3 Query
For the queries generated in Step-2, we will extract them and query HyperGraphRAG.
```bash
python Step_3.py
```

## Step-4 Evaluation
```bash
python Step_4.py
```
