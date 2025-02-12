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

### Agriculture
#### HyperGraph Construction
For the extracted contexts, we insert them into the HyperGraphRAG system.
```bash
nohup python script_insert.py --cls agriculture >> result_agriculture_insert.log 2>&1 &
```
#### HyperGraph-Guided Generation
For the queries collected, we will query HyperGraphRAG.
```bash
nohup python script_query.py --cls agriculture --level hard >> result_agriculture_hard_query.log 2>&1 &
nohup python script_query.py --cls agriculture --level medium >> result_agriculture_medium_query.log 2>&1 &
nohup python script_query.py --cls agriculture --level easy >> result_agriculture_easy_query.log 2>&1 &
```
#### Evaluation
Hard Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_hard.json --predictions_file output/HyperGraphRAG/agriculture/hard/agriculture_hard_result.json --output_score_path output/HyperGraphRAG/agriculture/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_hard.json --predictions_file output/LightRAG/agriculture/hard/agriculture_hard_result.json --output_score_path output/LightRAG/agriculture/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_hard.json --predictions_file output/GraphRAG/agriculture/hard/agriculture_hard_result.json --output_score_path output/GraphRAG/agriculture/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_hard.json --predictions_file output/StandardRAG/agriculture/hard/agriculture_hard_result.json --output_score_path output/StandardRAG/agriculture/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_hard.json --predictions_file output/NaiveGeneration/agriculture/hard/agriculture_hard_result.json --output_score_path output/NaiveGeneration/agriculture/hard/batch_eval_scores.json
```
Medium Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_medium.json --predictions_file output/HyperGraphRAG/agriculture/medium/agriculture_medium_result.json --output_score_path output/HyperGraphRAG/agriculture/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_medium.json --predictions_file output/LightRAG/agriculture/medium/agriculture_medium_result.json --output_score_path output/LightRAG/agriculture/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_medium.json --predictions_file output/GraphRAG/agriculture/medium/agriculture_medium_result.json --output_score_path output/GraphRAG/agriculture/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_medium.json --predictions_file output/StandardRAG/agriculture/medium/agriculture_medium_result.json --output_score_path output/StandardRAG/agriculture/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_medium.json --predictions_file output/NaiveGeneration/agriculture/medium/agriculture_medium_result.json --output_score_path output/NaiveGeneration/agriculture/medium/batch_eval_scores.json
```
Easy Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_easy.json --predictions_file output/HyperGraphRAG/agriculture/easy/agriculture_easy_result.json --output_score_path output/HyperGraphRAG/agriculture/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_easy.json --predictions_file output/LightRAG/agriculture/easy/agriculture_easy_result.json --output_score_path output/LightRAG/agriculture/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_easy.json --predictions_file output/GraphRAG/agriculture/easy/agriculture_easy_result.json --output_score_path output/GraphRAG/agriculture/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_easy.json --predictions_file output/StandardRAG/agriculture/easy/agriculture_easy_result.json --output_score_path output/StandardRAG/agriculture/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/agriculture/agriculture_easy.json --predictions_file output/NaiveGeneration/agriculture/easy/agriculture_easy_result.json --output_score_path output/NaiveGeneration/agriculture/easy/batch_eval_scores.json
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
nohup python script_query.py --cls cs --level hard >> result_cs_hard_query.log 2>&1 &
nohup python script_query.py --cls cs --level medium >> result_cs_medium_query.log 2>&1 &
nohup python script_query.py --cls cs --level easy >> result_cs_easy_query.log 2>&1 &
```
#### Evaluation
Hard Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/cs/cs_hard.json --predictions_file output/HyperGraphRAG/cs/hard/cs_hard_result.json --output_score_path output/HyperGraphRAG/cs/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_hard.json --predictions_file output/LightRAG/cs/hard/cs_hard_result.json --output_score_path output/LightRAG/cs/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_hard.json --predictions_file output/GraphRAG/cs/hard/cs_hard_result.json --output_score_path output/GraphRAG/cs/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_hard.json --predictions_file output/StandardRAG/cs/hard/cs_hard_result.json --output_score_path output/StandardRAG/cs/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_hard.json --predictions_file output/NaiveGeneration/cs/hard/cs_hard_result.json --output_score_path output/NaiveGeneration/cs/hard/batch_eval_scores.json
```
Medium Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/cs/cs_medium.json --predictions_file output/HyperGraphRAG/cs/medium/cs_medium_result.json --output_score_path output/HyperGraphRAG/cs/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_medium.json --predictions_file output/LightRAG/cs/medium/cs_medium_result.json --output_score_path output/LightRAG/cs/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_medium.json --predictions_file output/GraphRAG/cs/medium/cs_medium_result.json --output_score_path output/GraphRAG/cs/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_medium.json --predictions_file output/StandardRAG/cs/medium/cs_medium_result.json --output_score_path output/StandardRAG/cs/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_medium.json --predictions_file output/NaiveGeneration/cs/medium/cs_medium_result.json --output_score_path output/NaiveGeneration/cs/medium/batch_eval_scores.json
```
Easy Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/cs/cs_easy.json --predictions_file output/HyperGraphRAG/cs/easy/cs_easy_result.json --output_score_path output/HyperGraphRAG/cs/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_easy.json --predictions_file output/LightRAG/cs/easy/cs_easy_result.json --output_score_path output/LightRAG/cs/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_easy.json --predictions_file output/GraphRAG/cs/easy/cs_easy_result.json --output_score_path output/GraphRAG/cs/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_easy.json --predictions_file output/StandardRAG/cs/easy/cs_easy_result.json --output_score_path output/StandardRAG/cs/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/cs/cs_easy.json --predictions_file output/NaiveGeneration/cs/easy/cs_easy_result.json --output_score_path output/NaiveGeneration/cs/easy/batch_eval_scores.json
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
nohup python script_query.py --cls legal --level hard >> result_legal_hard_query.log 2>&1 &
nohup python script_query.py --cls legal --level medium >> result_legal_medium_query.log 2>&1 &
nohup python script_query.py --cls legal --level easy >> result_legal_easy_query.log 2>&1 &
```
#### Evaluation
Hard Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/legal/legal_hard.json --predictions_file output/HyperGraphRAG/legal/hard/legal_hard_result.json --output_score_path output/HyperGraphRAG/legal/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_hard.json --predictions_file output/LightRAG/legal/hard/legal_hard_result.json --output_score_path output/LightRAG/legal/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_hard.json --predictions_file output/GraphRAG/legal/hard/legal_hard_result.json --output_score_path output/GraphRAG/legal/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_hard.json --predictions_file output/StandardRAG/legal/hard/legal_hard_result.json --output_score_path output/StandardRAG/legal/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_hard.json --predictions_file output/NaiveGeneration/legal/hard/legal_hard_result.json --output_score_path output/NaiveGeneration/legal/hard/batch_eval_scores.json
```
Medium Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/legal/legal_medium.json --predictions_file output/HyperGraphRAG/legal/medium/legal_medium_result.json --output_score_path output/HyperGraphRAG/legal/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_medium.json --predictions_file output/LightRAG/legal/medium/legal_medium_result.json --output_score_path output/LightRAG/legal/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_medium.json --predictions_file output/GraphRAG/legal/medium/legal_medium_result.json --output_score_path output/GraphRAG/legal/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_medium.json --predictions_file output/StandardRAG/legal/medium/legal_medium_result.json --output_score_path output/StandardRAG/legal/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_medium.json --predictions_file output/NaiveGeneration/legal/medium/legal_medium_result.json --output_score_path output/NaiveGeneration/legal/medium/batch_eval_scores.json
```
Easy Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/legal/legal_easy.json --predictions_file output/HyperGraphRAG/legal/easy/legal_easy_result.json --output_score_path output/HyperGraphRAG/legal/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_easy.json --predictions_file output/LightRAG/legal/easy/legal_easy_result.json --output_score_path output/LightRAG/legal/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_easy.json --predictions_file output/GraphRAG/legal/easy/legal_easy_result.json --output_score_path output/GraphRAG/legal/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_easy.json --predictions_file output/StandardRAG/legal/easy/legal_easy_result.json --output_score_path output/StandardRAG/legal/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/legal/legal_easy.json --predictions_file output/NaiveGeneration/legal/easy/legal_easy_result.json --output_score_path output/NaiveGeneration/legal/easy/batch_eval_scores.json
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
nohup python script_query.py --cls mix --level hard >> result_mix_hard_query.log 2>&1 &
nohup python script_query.py --cls mix --level medium >> result_mix_medium_query.log 2>&1 &
nohup python script_query.py --cls mix --level easy >> result_mix_easy_query.log 2>&1 &
```
#### Evaluation
Hard Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/mix/mix_hard.json --predictions_file output/HyperGraphRAG/mix/hard/mix_hard_result.json --output_score_path output/HyperGraphRAG/mix/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_hard.json --predictions_file output/LightRAG/mix/hard/mix_hard_result.json --output_score_path output/LightRAG/mix/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_hard.json --predictions_file output/GraphRAG/mix/hard/mix_hard_result.json --output_score_path output/GraphRAG/mix/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_hard.json --predictions_file output/StandardRAG/mix/hard/mix_hard_result.json --output_score_path output/StandardRAG/mix/hard/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_hard.json --predictions_file output/NaiveGeneration/mix/hard/mix_hard_result.json --output_score_path output/NaiveGeneration/mix/hard/batch_eval_scores.json
```
Medium Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/mix/mix_medium.json --predictions_file output/HyperGraphRAG/mix/medium/mix_medium_result.json --output_score_path output/HyperGraphRAG/mix/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_medium.json --predictions_file output/LightRAG/mix/medium/mix_medium_result.json --output_score_path output/LightRAG/mix/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_medium.json --predictions_file output/GraphRAG/mix/medium/mix_medium_result.json --output_score_path output/GraphRAG/mix/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_medium.json --predictions_file output/StandardRAG/mix/medium/mix_medium_result.json --output_score_path output/StandardRAG/mix/medium/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_medium.json --predictions_file output/NaiveGeneration/mix/medium/mix_medium_result.json --output_score_path output/NaiveGeneration/mix/medium/batch_eval_scores.json
```
Easy Evaluation:
```bash
python script_eval.py --groundtruth_file datasets/questions/mix/mix_easy.json --predictions_file output/HyperGraphRAG/mix/easy/mix_easy_result.json --output_score_path output/HyperGraphRAG/mix/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_easy.json --predictions_file output/LightRAG/mix/easy/mix_easy_result.json --output_score_path output/LightRAG/mix/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_easy.json --predictions_file output/GraphRAG/mix/easy/mix_easy_result.json --output_score_path output/GraphRAG/mix/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_easy.json --predictions_file output/StandardRAG/mix/easy/mix_easy_result.json --output_score_path output/StandardRAG/mix/easy/batch_eval_scores.json
python script_eval.py --groundtruth_file datasets/questions/mix/mix_easy.json --predictions_file output/NaiveGeneration/mix/easy/mix_easy_result.json --output_score_path output/NaiveGeneration/mix/easy/batch_eval_scores.json
```







