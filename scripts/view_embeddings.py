import os
import pickle

EMBEDDINGS_FILE = "data/embeddings.pkl"

def main():
    if not os.path.exists(EMBEDDINGS_FILE):
        print(f"File not found: {EMBEDDINGS_FILE}")
        return
        
    with open(EMBEDDINGS_FILE, "rb") as f:
        data = pickle.load(f)
        
    print(f"--- Loaded {len(data)} embeddings from {EMBEDDINGS_FILE} ---")
    for note_id, vector in data.items():
        print(f"ID: {note_id} | Shape: {vector.shape} | Type: {type(vector)}")
        
if __name__ == "__main__":
    main()
