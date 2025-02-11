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
nohup python script_query.py --cls hypertension --level hard >> result_hypertension_hard_query.log 2>&1 &
nohup python script_query.py --cls hypertension --level medium >> result_hypertension_medium_query.log 2>&1 &
nohup python script_query.py --cls hypertension --level easy >> result_hypertension_easy_query.log 2>&1 &
```
#### Evaluation
Hard Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_hard.json --predictions_file output/HyperGraphRAG/hypertension/hard/hypertension_hard_result.json --output_score_path output/HyperGraphRAG/hypertension/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_hard.json --predictions_file output/LightRAG/hypertension/hard/hypertension_hard_result.json --output_score_path output/LightRAG/hypertension/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_hard.json --predictions_file output/GraphRAG/hypertension/hard/hypertension_hard_result.json --output_score_path output/GraphRAG/hypertension/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_hard.json --predictions_file output/StandardRAG/hypertension/hard/hypertension_hard_result.json --output_score_path output/StandardRAG/hypertension/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_hard.json --predictions_file output/NaiveGeneration/hypertension/hard/hypertension_hard_result.json --output_score_path output/NaiveGeneration/hypertension/hard/batch_eval_scores.json
```
Medium Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_medium.json --predictions_file output/HyperGraphRAG/hypertension/medium/hypertension_medium_result.json --output_score_path output/HyperGraphRAG/hypertension/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_medium.json --predictions_file output/LightRAG/hypertension/medium/hypertension_medium_result.json --output_score_path output/LightRAG/hypertension/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_medium.json --predictions_file output/GraphRAG/hypertension/medium/hypertension_medium_result.json --output_score_path output/GraphRAG/hypertension/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_medium.json --predictions_file output/StandardRAG/hypertension/medium/hypertension_medium_result.json --output_score_path output/StandardRAG/hypertension/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_medium.json --predictions_file output/NaiveGeneration/hypertension/medium/hypertension_medium_result.json --output_score_path output/NaiveGeneration/hypertension/medium/batch_eval_scores.json
```
Easy Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_easy.json --predictions_file output/HyperGraphRAG/hypertension/easy/hypertension_easy_result.json --output_score_path output/HyperGraphRAG/hypertension/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_easy.json --predictions_file output/LightRAG/hypertension/easy/hypertension_easy_result.json --output_score_path output/LightRAG/hypertension/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_easy.json --predictions_file output/GraphRAG/hypertension/easy/hypertension_easy_result.json --output_score_path output/GraphRAG/hypertension/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_easy.json --predictions_file output/StandardRAG/hypertension/easy/hypertension_easy_result.json --output_score_path output/StandardRAG/hypertension/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/hypertension/hypertension_easy.json --predictions_file output/NaiveGeneration/hypertension/easy/hypertension_easy_result.json --output_score_path output/NaiveGeneration/hypertension/easy/batch_eval_scores.json
```















