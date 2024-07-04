import os
import pickle as pkl
import threading
from itertools import combinations
import networkx as nx
from src.availability_evaluation import calculate_availability
import pandas as pd


def evaluate_availability_single(G, source, target, A_dic):
    try:
        node_labels = nx.get_node_attributes(G, 'label')
        if not node_labels:
            raise nx.NetworkXError
    except nx.NetworkXError:
        node_labels = nx.get_node_attributes(G, 'name')

    city_labels = {i: label for i, label in enumerate(node_labels.values())}
    G = nx.relabel_nodes(G, city_labels)

    result, combined_results = calculate_availability(G, source, target, A_dic)

    # Save result
    if isinstance(A_dic, list):
        result_df = pd.DataFrame(result, columns=['source', 'target', *[f'{val} Availability' for val in A_dic]])
    elif isinstance(A_dic, dict):
        result_df = pd.DataFrame(result, columns=['source', 'target', ' Availability'])
    result_df.to_csv('availability_evaluation_multithreading.csv', index=False)


def evaluate_availability_multiple(G, R, A_dic):
    try:
        node_labels = nx.get_node_attributes(G, 'label')
        if not node_labels:
            raise nx.NetworkXError
    except nx.NetworkXError:
        node_labels = nx.get_node_attributes(G, 'name')


    city_labels = {i: label for i, label in enumerate(node_labels.values())}
    G = nx.relabel_nodes(G, city_labels)

    adjusted_pairs = [(city_labels[pair[0]], city_labels[pair[1]]) for pair in R]

    result_accumulator = []

    # Function to process each pair
    def process_pair(pair, result_dict):
        source_node, target_node = pair
        result, combined_results = calculate_availability(G, source_node, target_node, A_dic)
        result_dict[pair] = (result)  # Store result and si

    # Dictionary to store the results of each thread
    thread_results = {}

    # Create threads for each pair and start them
    threads = []
    for pair in adjusted_pairs:
        thread_results[pair] = None  # Initialize result placeholder
        thread = threading.Thread(target=process_pair, args=(pair, thread_results))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Collect results and calculate total simulation time
    for pair, (result) in thread_results.items():
        result_accumulator.extend(result)
    return result_accumulator

    # Save result
    if isinstance(A_dic, list):
        result_df = pd.DataFrame(result_accumulator, columns=['source', 'target', *[f'{val} Availability' for val in A_dic]])
    elif isinstance(A_dic, dict):
        result_df = pd.DataFrame(result_accumulator, columns=['source', 'target', ' Availability'])
    result_df.to_csv('availability_evaluation_multithreading.csv', index=False)


if __name__ == "__main__":

    topologies_path = os.path.join(os.getcwd(), 'topologies')
    folder_path = os.path.join(topologies_path, 'Abilene')

    with open(os.path.join(folder_path, 'Pickle_' + 'Abilene' + '.pickle'), 'rb') as f:
        graph = pkl.load(f)
    G = graph[0]

    source = 'New York'
    target = 'Atlanta'

    A_dic = [0.9, 0.99, 0.999, 0.9999]

    R = list(combinations(list(G.nodes), 2))

    # result_accumulator = evaluate_availability_multiple(G, R, A_dic)
    result_accumulator = evaluate_availability_single(G, source, target, A_dic)
    # Save result

    if isinstance(A_dic, list):
        result_df = pd.DataFrame(result_accumulator,
                                 columns=['source', 'target', *[f'{val} Availability' for val in A_dic]])
    elif isinstance(A_dic, dict):
        result_df = pd.DataFrame(result_accumulator, columns=['source', 'target', ' Availability'])
    result_df.to_csv('availability_evaluation_multithreading.csv', index=False)