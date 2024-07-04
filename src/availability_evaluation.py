"""
    Consist of all availability evaluation methods
"""
from datetime import datetime
import sys
import tracemalloc
from itertools import combinations
import copy
import pandas as pd
import os
import pickle as pkl
import networkx as nx
import time
from matplotlib import pyplot as plt
from src.cutsets import minimalcuts


# Find the most repeated node in cut sets with lowest cardinality
# Starting Node
def most_repeated_node(minimal_sets):
    min_cardinality = min(len(min_set) for min_set in minimal_sets)
    min_cardinality_sets = [min_set for min_set in minimal_sets if len(min_set) == min_cardinality]

    nodes_count = {}
    for min_set in min_cardinality_sets:
        for node in min_set:
            if node in nodes_count:
                nodes_count[node] += 1
            else:
                nodes_count[node] = 1

    most_repeated_node = max(nodes_count, key=nodes_count.get)
    return most_repeated_node


# Check if there is direct path between s and t
def is_direct_path(G, src_, dst_):
    return nx.shortest_path_length(G, source=src_, target=dst_) == 1


# Check if there is path between source and target
def has_path(G, src_, dst_):
    return nx.has_path(G, source=src_, target=dst_)


# Modify the graph based on the existence or failure of the node
def manipulate_graph(graph, nodes):
    manipulated_graph = copy.deepcopy(graph)

    for node in nodes:
        node = int(node)
        # If node exist, remove node and add edge
        if node > 0:
            neighbors = list(manipulated_graph.neighbors(node))
            manipulated_graph.remove_node(node)
            for neighbor1 in neighbors:
                for neighbor2 in neighbors:
                    if neighbor1 != neighbor2 and not manipulated_graph.has_edge(neighbor1, neighbor2):
                        manipulated_graph.add_edge(neighbor1, neighbor2)

        # If node failed, remove it
        elif node < 0:
            manipulated_graph.remove_node(node * (-1))
    return manipulated_graph


# Return a result dictionary mapping nodes to values: -1 for branching, 1 for direct paths, and 0 for failure.
def evaluate_nodes(graph, source, target, nodes_to_evaluate):
    result = {}  # Initializes an empty dictionary

    # Evaluate multiple node
    def evaluate_multiple_node(updated_graph, combined_nodes):

        try:
            result[f'{combined_nodes}'] = 1 if is_direct_path(updated_graph, source, target) else -1 if has_path(
                updated_graph, source, target) else 0
        except nx.NetworkXNoPath:
            result[f'{combined_nodes}'] = 0

    if isinstance(nodes_to_evaluate, int):  # Single node case, only for the most repeated node

        with_node = manipulate_graph(graph, [nodes_to_evaluate])
        result[f'{nodes_to_evaluate}'] = 1 if is_direct_path(with_node, source, target) else -1 if has_path(
            with_node, source, target) else 0
        without_node = manipulate_graph(graph, [nodes_to_evaluate * (-1)])
        result[f'{nodes_to_evaluate * (-1)}'] = 1 if is_direct_path(without_node, source, target) else -1 if has_path(
            without_node, source, target) else 0

    elif isinstance(nodes_to_evaluate, list):  # Multiple nodes case

        for combination in nodes_to_evaluate:
            updated_graph = manipulate_graph(graph, combination)
            evaluate_multiple_node(updated_graph, combination)

    return result


# Returns the total availability of the system
def availability_evaluation(one_results, zero_results, component_data, source_availability, target_availability):
    if len(one_results) > len(zero_results):
        if len(zero_results) != 0:

            unavailability = evaluate_expression(zero_results, component_data)
            availability = 1 - unavailability

            return availability * source_availability * target_availability
        else:
            availability = evaluate_expression(one_results, component_data)

            return availability * source_availability * target_availability

    elif len(one_results) < len(zero_results):
        if len(one_results) != 0:

            availability = evaluate_expression(one_results, component_data)

            return availability * source_availability * target_availability
        else:
            unavailability = evaluate_expression(zero_results, component_data)
            availability = 1 - unavailability

            return availability * source_availability * target_availability

    else:


        availability = evaluate_expression(one_results, component_data)

        return availability * source_availability * target_availability


# Substitute each node with its availability value
def value_substitution(char, component_data):
    char = int(char)
    if char < 0:
        return 1 - component_data.get(char * (-1))
    elif char > 0:
        return component_data.get(char)


# Calculates the total value of a list of words based on substitution values.
def evaluate_expression(results, component_data):
    total_value = 0
    for word in results:
        item_list = eval(word)
        word_value = 1
        for char in item_list:
            substituted_value = value_substitution(char, component_data)
            word_value *= substituted_value
        total_value += word_value
    return total_value


# Load data from a pickle file
def read_graph(directory, top):
    with open(os.path.join(directory, 'Pickle_' + top + '.pickle'), 'rb') as handle:
        f = pkl.load(handle)
    G = f[0]
    pos = f[1]
    lable = f[2]
    return G, pos, lable

# A methods to evaluate the topology
def process_topology(G, source_node, target_node, A_dic):
    data = []
    availabilities = {}  # Avalibilities

    # Check if there is no direct connection between the source and target nodes with one hop

    if nx.shortest_path_length(G, source=source_node, target=target_node) > 1:

        # Find all minimal cut sets
        all_cut_sets = minimalcuts(G, source_node, target_node)

        # Find the most repeated node in the minimal cut sets
        # Starting node
        most_repeated = most_repeated_node(all_cut_sets)

        # Initializing two lists to store nodes with values 1: direct path and 0: no path
        zero_results = []
        one_results = []

        # Evaluate first node
        evaluate_result = evaluate_nodes(G, source_node, target_node, int(most_repeated))



        # List to store unique nodes from cut sets excluding the most repeated node
        unique_nodes = []

        # Iterating through each cut set
        for cut_set in all_cut_sets:
            for node in cut_set:
                if node != most_repeated and node not in unique_nodes:
                    unique_nodes.append(node)

        previous_evaluation_nodes = set()
        # Iterating over unique nodes
        for node in unique_nodes:
            updated_evaluation_result = []

            # First iteration
            if not previous_evaluation_nodes:
                for key, value in evaluate_result.items():
                    if value == -1:
                        updated_evaluation_result.append([key, str(node)])
                        updated_evaluation_result.append([key, str(int(node * (-1)))])

                    iterated_nodes = evaluate_nodes(G, source_node, target_node, updated_evaluation_result)


                # Extract the keys from the evaluation result ( most repeated node evaluation )
                nodes = list(evaluate_result.keys())

                # Loop through the nodes and check if they are in the one or zero result
                for node in nodes:
                    if evaluate_result[node] == 1:
                        one_results.append(f"['{node}']")
                    elif evaluate_result[node] == 0:
                        zero_results.append(f"['{node}']")

                for key, value in iterated_nodes.items():
                    if value == -1:
                        previous_evaluation_nodes.add(key)
                    if value == 1:
                        one_results.append(key)
                    if value == 0:
                        zero_results.append(key)


            else:
                new_evaluation_nodes = set()
                # Using the evaluate_nodes from the previous iteration

                for s in previous_evaluation_nodes:
                    new_set = eval(s)  # Converting string representation of set to actual set
                    new_set2 = eval(s)
                    new_set.append(str(node))
                    new_set2.append(str(int(node * (-1))))
                    updated_evaluation_result.append(new_set)
                    updated_evaluation_result.append(new_set2)
                    iterated_nodes = evaluate_nodes(G, source_node, target_node, updated_evaluation_result)



                for key, value in iterated_nodes.items():
                    if value == -1:
                        new_evaluation_nodes.add(key)
                    if value == 1:
                        one_results.append(key)
                    if value == 0:
                        zero_results.append(key)
                previous_evaluation_nodes = new_evaluation_nodes




        combined_results = one_results + zero_results


        if isinstance(A_dic, dict):

            source_availability = A_dic.get(source_node)
            target_availability = A_dic.get(target_node)

            # Construct component_data with node availabilities
            component_data = {n: A_dic.get(n, A_dic.values()) for n in G.nodes()}
            # Calculate availability for each component value
            availabilities = availability_evaluation(one_results, zero_results, component_data,
                                                     source_availability, target_availability)
            print('Overall Availability :', availabilities)
            data.append((source_node, target_node, availabilities))


        elif isinstance(A_dic, list):

            for component_value in A_dic:
                component_data = {node: component_value for node in G.nodes()}
                # source and target availabilities for the current component value
                source_availability = component_value
                target_availability = component_value
                availabilities[component_value] = availability_evaluation(one_results, zero_results, component_data,
                                                                          source_availability, target_availability)
                print('Avalibility with flow avalibilities', component_value, 'is', availabilities[component_value])

            data.append((source_node, target_node, *[availabilities[val] for val in A_dic]))
        else:
            print("Invalid input format")
        # data.append((source_node, target_node, *[availabilities[val] for val in A_dic]))
        return data, combined_results

    else:
        if isinstance(A_dic, dict):
            source_availability = A_dic.get(source_node)
            target_availability = A_dic.get(target_node)
            availabilities = source_availability * target_availability
            print('Overall Availability :', availabilities)
            data.append((source_node, target_node, availabilities))

        elif isinstance(A_dic, list):
            for component_value in A_dic:
                source_availability = component_value
                target_availability = component_value
                availabilities[component_value] = source_availability * target_availability
                print('Avalibility with flow avalibilities', component_value, 'is', availabilities[component_value])

            data.append((source_node, target_node, *[availabilities[val] for val in A_dic]))

        return data, []


# The main function to calculate the availability of the system
def calculate_availability(G, source, target, A_dic):
    # Get the nodes of G
    nodes = list(G.nodes())

    relabel_mapping = {nodes[i]: i + 1 for i in range(len(nodes))}

    # Relabel the nodes of G
    G = nx.relabel_nodes(G, relabel_mapping)


    # Find the new labels for source and target
    new_source = None
    new_target = None
    for node, label in relabel_mapping.items():
        if node == source:
            new_source = label
        elif node == target:
            new_target = label



    if isinstance(A_dic, dict):

        # Creating a new A_dic with relabeled node numbers
        A_dic_relabeled = {relabel_mapping[node]: value for node, value in A_dic.items()}

        result, combined_results = process_topology(G, new_source, new_target, A_dic_relabeled)

    elif isinstance(A_dic, list):
        result, combined_results = process_topology(G, new_source, new_target, A_dic)

    return result,combined_results



