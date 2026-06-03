import json
import sys
from pathlib import Path
from collections import defaultdict

DAW_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = Path(__file__).resolve().parent / "dataset-full.jsonl"
OUT_PATH = Path(__file__).resolve().parent / "module_weights.json"

# Módulos que ignoramos como "nodos de contenido" (ya que son contenedores estructurales)
SKIP_TAGS = {'et_pb_section', 'et_pb_row', 'et_pb_row_inner', 'et_pb_column', 'et_pb_column_inner'}

def get_leaf_sequence(tree_nodes):
    """Extrae la secuencia plana de módulos de contenido de un árbol."""
    seq = []
    def walk(nodes):
        for node in nodes:
            tag = node.get("tag")
            if tag not in SKIP_TAGS:
                seq.append(tag)
            walk(node.get("children", []))
    walk(tree_nodes)
    return seq

def train():
    if not DATASET_PATH.exists():
        print(f"Error: {DATASET_PATH} no existe.")
        sys.exit(1)

    print(f"[ML-TRAINER] Cargando dataset: {DATASET_PATH.name}...")
    
    # bigrams[current][next] = count
    bigrams = defaultdict(lambda: defaultdict(int))
    start_nodes = defaultdict(int)
    module_frequencies = defaultdict(int)
    total_templates = 0

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                rec = json.loads(line)
            except:
                continue
            
            tree = rec.get("tree", [])
            seq = get_leaf_sequence(tree)
            
            if not seq:
                continue
                
            total_templates += 1
            
            # Start node probability
            start_nodes[seq[0]] += 1
            
            # Bigram transitions
            for i in range(len(seq) - 1):
                current_mod = seq[i]
                next_mod = seq[i+1]
                bigrams[current_mod][next_mod] += 1
                module_frequencies[current_mod] += 1
            
            # Add last module
            module_frequencies[seq[-1]] += 1
            bigrams[seq[-1]]["END"] += 1

    print(f"[ML-TRAINER] Entrenando con {total_templates} templates.")

    # Convertir conteos a probabilidades
    model = {
        "start_probabilities": {},
        "transitions": {},
        "global_frequencies": {}
    }

    # Start Probs
    total_starts = sum(start_nodes.values())
    for mod, count in start_nodes.items():
        model["start_probabilities"][mod] = round(count / total_starts, 4)

    # Transition Probs
    for current_mod, next_mods in bigrams.items():
        total_transitions = sum(next_mods.values())
        model["transitions"][current_mod] = {}
        for next_mod, count in next_mods.items():
            model["transitions"][current_mod][next_mod] = round(count / total_transitions, 4)
            
    # Global Frequencies
    total_mods = sum(module_frequencies.values())
    for mod, count in module_frequencies.items():
        model["global_frequencies"][mod] = round(count / total_mods, 4)

    # Sort everything for readability
    model["start_probabilities"] = dict(sorted(model["start_probabilities"].items(), key=lambda x: x[1], reverse=True))
    model["global_frequencies"] = dict(sorted(model["global_frequencies"].items(), key=lambda x: x[1], reverse=True))
    for k in model["transitions"]:
        model["transitions"][k] = dict(sorted(model["transitions"][k].items(), key=lambda x: x[1], reverse=True))

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2)

    print(f"[ML-TRAINER] Modelo exportado a {OUT_PATH.name} ({len(model['transitions'])} nodos)")

if __name__ == '__main__':
    train()
