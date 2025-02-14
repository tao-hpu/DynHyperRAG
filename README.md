# HyperGraphRAG

## Dependence
```bash
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag
pip install torch==2.3.0
pip install -r requirements.txt
```

## Dataset Preparation

We construct the GraphRAG evaluation based on [Hypertension](https://academic.oup.com/eurheartj/article/45/38/3912/7741010?login=false) and [UltraDomain](https://huggingface.co/datasets/TommyChien/UltraDomain) (Agriculture, Leagal, CS, Mix).

You can download processed datasets from [TeraBox](https://1024terabox.com/s/1rICU6rM64Oezq60GoXJoJg) or [Baidu Netdisk](https://pan.baidu.com/s/1bSuazL0fhR_Xs2Mg1hxB6g?pwd=45c1), and set the dataset path in `datasets/`.

```
HyperGraphRAG/
└── datasets/
    ├── contexts/   
        ├── hypertension_contexts.json   
        ├── agriculture_contexts.json    
        ├── cs_contexts.json                  
        ├── legal_contexts.json                    
        └── mix_contexts.json    
    └── questions/           
        ├── hypertension/                     
            ├── hypertension_easy.json            
            ├── hypertension_medium.json         
            └── hypertension_hard.json     
        ├── agriculture/                     
            ├── agriculture_easy.json            
            ├── agriculture_medium.json         
            └── agriculture_hard.json 
        ├── cs/                     
            ├── cs_easy.json            
            ├── cs_medium.json         
            └── cs_hard.json 
        ├── legal/                     
            ├── legal_easy.json            
            ├── legal_medium.json         
            └── legal_hard.json 
        └── mix/                     
            ├── mix_easy.json            
            ├── mix_medium.json         
            └── mix_hard.json                                 
```

## HyperGraphRAG Process

### Hypertension
#### HyperGraph Construction
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
nohup python script_insert.py --cls hypertension >> result_hypertension_insert.log 2>&1 &
```
#### HyperGraph-Guided Generation
For the queries collected, we will query HyperGraphRAG.
```bash
nohup python script_query.py --cls hypertension --level easy >> result_hypertension_easy_query.log 2>&1 &
nohup python script_query.py --cls hypertension --level medium >> result_hypertension_medium_query.log 2>&1 &
nohup python script_query.py --cls hypertension --level hard >> result_hypertension_hard_query.log 2>&1 &
```
#### Evaluation
Three kinds of Source and Overall Evaluation:
```bash
python script_eval.py --cls hypertension --level easy --method HyperGraphRAG
python script_eval.py --cls hypertension --level medium --method HyperGraphRAG
python script_eval.py --cls hypertension --level hard --method HyperGraphRAG
python script_eval.py --cls hypertension --level overall --method HyperGraphRAG
```

### Agriculture
#### HyperGraph Construction
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
nohup python script_insert.py --cls agriculture >> result_agriculture_insert.log 2>&1 &
```
#### HyperGraph-Guided Generation
For the queries collected, we will query HyperGraphRAG.
```bash
nohup python script_query.py --cls agriculture --level easy >> result_agriculture_easy_query.log 2>&1 &
nohup python script_query.py --cls agriculture --level medium >> result_agriculture_medium_query.log 2>&1 &
nohup python script_query.py --cls agriculture --level hard >> result_agriculture_hard_query.log 2>&1 &
```
#### Evaluation
Three kinds of Source and Overall Evaluation:
```bash
python script_eval.py --cls agriculture --level easy --method HyperGraphRAG
python script_eval.py --cls agriculture --level medium --method HyperGraphRAG
python script_eval.py --cls agriculture --level hard --method HyperGraphRAG
python script_eval.py --cls agriculture --level overall --method HyperGraphRAG
```

### CS
#### HyperGraph Construction
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
nohup python script_insert.py --cls cs >> result_cs_insert.log 2>&1 &
```
#### HyperGraph-Guided Generation
For the queries collected, we will query HyperGraphRAG.
```bash
nohup python script_query.py --cls cs --level easy >> result_cs_easy_query.log 2>&1 &
nohup python script_query.py --cls cs --level medium >> result_cs_medium_query.log 2>&1 &
nohup python script_query.py --cls cs --level hard >> result_cs_hard_query.log 2>&1 &
```
#### Evaluation
Three kinds of Source and Overall Evaluation:
```bash
python script_eval.py --cls cs --level easy --method HyperGraphRAG
python script_eval.py --cls cs --level medium --method HyperGraphRAG
python script_eval.py --cls cs --level hard --method HyperGraphRAG
python script_eval.py --cls cs --level overall --method HyperGraphRAG
```

### Legal
#### HyperGraph Construction
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
nohup python script_insert.py --cls legal >> result_legal_insert.log 2>&1 &
```
#### HyperGraph-Guided Generation
For the queries collected, we will query HyperGraphRAG.
```bash
nohup python script_query.py --cls legal --level easy >> result_legal_easy_query.log 2>&1 &
nohup python script_query.py --cls legal --level medium >> result_legal_medium_query.log 2>&1 &
nohup python script_query.py --cls legal --level hard >> result_legal_hard_query.log 2>&1 &
```
#### Evaluation
Three kinds of Source and Overall Evaluation:
```bash
python script_eval.py --cls legal --level easy --method HyperGraphRAG
python script_eval.py --cls legal --level medium --method HyperGraphRAG
python script_eval.py --cls legal --level hard --method HyperGraphRAG
python script_eval.py --cls legal --level overall --method HyperGraphRAG
```


### Mix
#### HyperGraph Construction
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
nohup python script_insert.py --cls mix >> result_mix_insert.log 2>&1 &
```
#### HyperGraph-Guided Generation
For the queries collected, we will query HyperGraphRAG.
```bash
nohup python script_query.py --cls mix --level easy >> result_mix_easy_query.log 2>&1 &
nohup python script_query.py --cls mix --level medium >> result_mix_medium_query.log 2>&1 &
nohup python script_query.py --cls mix --level hard >> result_mix_hard_query.log 2>&1 &
```
#### Evaluation
Three kinds of Source and Overall Evaluation:
```bash
python script_eval.py --cls mix --level easy --method HyperGraphRAG
python script_eval.py --cls mix --level medium --method HyperGraphRAG
python script_eval.py --cls mix --level hard --method HyperGraphRAG
python script_eval.py --cls mix --level overall --method HyperGraphRAG
```





