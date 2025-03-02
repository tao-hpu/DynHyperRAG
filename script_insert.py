import os
import json
import time
from hypergraphrag import HyperGraphRAG
import argparse
os.environ["OPENAI_API_KEY"] = open("openai_api_key.txt").read().strip()

def insert_knowledge(rag, unique_contexts):
    retries = 0
    max_retries = 10
    while retries < max_retries:
        try:
            rag.insert(unique_contexts)
            break
        except Exception as e:
            retries += 1
            print(f"Insertion failed, retrying ({retries}/{max_retries}), error: {e}")
            time.sleep(10)
    if retries == max_retries:
        print("Insertion failed after exceeding the maximum number of retries")

parser = argparse.ArgumentParser()
parser.add_argument("--cls", type=str, default="hypertension")
args = parser.parse_args()

rag = HyperGraphRAG(working_dir=f"expr/{args.cls}")

with open(f"datasets/contexts/{args.cls}_contexts.json", mode="r") as f:
    unique_contexts = json.load(f)
    
insert_knowledge(rag, unique_contexts)



