import os
import networkx as nx
import numpy as np
from nodevectors import ProNE  

def get_code_graph_embedding(code_snippet, embed_dim=16):
    # Create a new directed graph.
    graph = nx.DiGraph()

    # Split the code snippet into tokens.
    tokens = code_snippet.split()

    # Add the tokens as nodes to the graph.
    for token in tokens:
        graph.add_node(token)

    # Add edges between adjacent tokens.
    for i in range(len(tokens) - 1):
        graph.add_edge(tokens[i], tokens[i + 1])

    # Generate embedding using ProNE
    g2v = ProNE(n_components=embed_dim)
    g2v.fit(graph)  # Fit ProNE on the entire graph

    # Get the embeddings for each node, padding/truncating to ensure uniform size
    embeddings = []
    for node in graph.nodes:
        node_embedding = g2v.predict(node)
        if len(node_embedding) > embed_dim:
            node_embedding = node_embedding[:embed_dim]  # Truncate if larger than embed_dim
        elif len(node_embedding) < embed_dim:
            node_embedding = np.pad(node_embedding, (0, embed_dim - len(node_embedding)), mode='constant')
        embeddings.append(node_embedding)

    # Aggregate embeddings (mean) to represent the entire graph as a single vector
    graph_embedding = np.mean(embeddings, axis=0)

    return graph_embedding

def calculate_similarity(code_snippet_1, code_snippet_2, embed_dim=16):
    # Get the embeddings representing the code snippets.
    code_embedding_1 = get_code_graph_embedding(code_snippet_1, embed_dim=embed_dim)
    code_embedding_2 = get_code_graph_embedding(code_snippet_2, embed_dim=embed_dim)

    # Calculate Manhattan distance between the two embeddings.
    similarity = np.linalg.norm(code_embedding_1 - code_embedding_2, ord=1)

    # Return the similarity (lower is more similar).
    return similarity

# Define the path to the IR-Plag-Dataset folder
dataset_path = "D:/MyITSAcademia2-Season1/RPL/code_repository/codesim/IR-Plag-Dataset/"

# Define a list of similarity thresholds to iterate over
similarity_thresholds = [0.1, 0.3, 0.6]

# Initialize variables to keep track of the best result
best_threshold = 0
best_accuracy = 0

# Initialize counters
TP = 0
FP = 0
FN = 0

# Loop through each similarity threshold and calculate accuracy
for SIMILARITY_THRESHOLD in similarity_thresholds:
    # Initialize the counters
    total_cases = 0
    over_threshold_cases_plagiarized = 0
    over_threshold_cases_non_plagiarized = 0
    cases_plag = 0
    cases_non_plag = 0

    # Loop through each subfolder in the dataset
    for folder_name in os.listdir(dataset_path):
        folder_path = os.path.join(dataset_path, folder_name)
        if os.path.isdir(folder_path):
            # Find the Java file in the original folder
            original_path = os.path.join(folder_path, 'original')
            java_files = [f for f in os.listdir(original_path) if f.endswith('.java')]
            if len(java_files) == 1:
                java_file = java_files[0]
                with open(os.path.join(original_path, java_file), 'r') as f:
                    code1 = f.read()

                # Loop through each subfolder in the plagiarized and non-plagiarized folders
                for subfolder_name in ['plagiarized', 'non-plagiarized']:
                    subfolder_path = os.path.join(folder_path, subfolder_name)
                    if os.path.isdir(subfolder_path):
                        # Loop through each Java file in the subfolder
                        for root, dirs, files in os.walk(subfolder_path):
                            for java_file in files:
                                if java_file.endswith('.java'):
                                    with open(os.path.join(root, java_file), 'r') as f:
                                        code2 = f.read()

                                    # Calculate the similarity ratio using Manhattan distance
                                    similarity_ratio = calculate_similarity(code1, code2)

                                    # Update counters based on similarity ratio
                                    if subfolder_name == 'plagiarized':
                                        cases_plag += 1
                                        if similarity_ratio <= SIMILARITY_THRESHOLD:
                                            over_threshold_cases_plagiarized += 1
                                    elif subfolder_name == 'non-plagiarized':
                                        cases_non_plag += 1
                                        if similarity_ratio > SIMILARITY_THRESHOLD:
                                            over_threshold_cases_non_plagiarized += 1
                                    total_cases += 1
                                    # Update the counters based on the similarity ratio
                                    if subfolder_name == 'plagiarized':
                                        cases_plag += 1
                                        if similarity_ratio <= SIMILARITY_THRESHOLD:
                                            TP += 1  # True positive: plagiarized and identified as plagiarized
                                        else:
                                            FN += 1  # False negative: plagiarized but identified as non-plagiarized
                                    elif subfolder_name == 'non-plagiarized':
                                        cases_non_plag += 1
                                        if similarity_ratio > SIMILARITY_THRESHOLD:
                                            over_threshold_cases_non_plagiarized += 1
                                        else:
                                            FP += 1  # False positive: non-plagiarized but identified as plagiarized
            else:
                print(f"Error: Found {len(java_files)} Java files in {original_path} for {folder_name}")

    # Calculate accuracy for the current threshold
    if total_cases > 0:
        accuracy = (over_threshold_cases_non_plagiarized + over_threshold_cases_plagiarized) / total_cases
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = SIMILARITY_THRESHOLD

    # Calculate precision and recall
    if TP + FP > 0:
        precision = TP / (TP + FP)
    else:
        precision = 0

    if TP + FN > 0:
        recall = TP / (TP + FN)
    else:
        recall = 0

    # Calculate F-measure
    if precision + recall > 0:
        f_measure = 2 * (precision * recall) / (precision + recall)
    else:
        f_measure = 0

# Print the best threshold and accuracy
print(f"{os.path.basename(__file__)} - The best threshold is {best_threshold} with an accuracy of {best_accuracy:.2f}, Precision: {precision:.2f}, Recall: {recall:.2f}, F-measure: {f_measure:.2f}")
