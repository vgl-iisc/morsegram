import networkx as nx
import networkx.algorithms.community as community
from core import utils
from settings import Config
import matplotlib.pyplot as plt
import os
import shutil
import numpy as np


def draw_network(adj_list):
    '''
    Draw network using networkx
    @param adj_list: adjacency list
    '''
    G = nx.Graph()
    for i in range(len(adj_list)):
        for j in adj_list[i]:
            G.add_edge(i, j)
    nx.draw(G, with_labels=True)
    plt.show()


def adj_matrix(adj_list):
    '''
    Adjacency matrix
    @param adj_list: adjacency list
    '''
    n = len(adj_list)
    A = np.zeros((n, n))
    for i in range(n):
        for j in adj_list[i]:
            A[i, j] = 1
    return A


def deg_matrix(adj_list):
    '''
    Degree matrix
    @param adj_list: adjacency list
    '''
    n = len(adj_list)
    D = np.zeros((n, n))
    for i in range(n):
        D[i, i] = len(adj_list[i])
    return D


def lap_matrix(adj_list):
    '''
    Laplacian matrix
    @param adj_list: adjacency list
    '''
    return deg_matrix(adj_list) - adj_matrix(adj_list)


def num_components(adj_list):
    '''
    Number of connected components
    @param adj_list: adjacency list
    '''
    # eigenvalues of laplacian matrix
    L = lap_matrix(adj_list)
    # print("Laplacian matrix:", L)
    eigvals, eigvecs = np.linalg.eig(L)

    # plot eigenvalues for displaying eigen gap
    plt.figure(figsize=(10, 10))
    plt.plot(eigvals, 'o')
    plt.xlabel("Index")
    plt.ylabel("Eigenvalue")
    plt.show()

    # plot eigenvalues histogram
    plt.figure(figsize=(10, 10))
    plt.hist(eigvals, bins=100)
    plt.xlabel("Eigenvalue")
    plt.ylabel("Frequency")
    plt.show()

    # print("Eigenvalues:", eigvals)

    # print number of imaginary eigenvalues
    print("Number of imaginary eigenvalues:", len([x for x in eigvals if np.iscomplex(x)]))
    for x in eigvals:
        if np.iscomplex(x):
            print(x)

    # compute fiedler vector
    # fiedler vector is the eigenvector corresponding to the second smallest eigenvalue
    # second smallest eigenvalue is the eigen gap
    sorted_eigvals = np.sort(eigvals)
    # print("sorted eigenvalues:", sorted_eigvals)

    # scatter plot of eigenvalues
    plt.figure(figsize=(10, 10))
    # x - real part of eigenvalues
    # y - imaginary part of eigenvalues
    plt.scatter(np.real(eigvals), np.imag(eigvals))
    plt.xlabel("Real part")
    plt.ylabel("Imaginary part")
    plt.show()

    # plot sorted eigenvalues
    plt.figure(figsize=(10, 10))
    # name of the plot
    plt.title("Sorted eigenvalues")
    plt.plot(sorted_eigvals)
    plt.xlabel("Index")
    plt.ylabel("Eigenvalue")
    plt.show()

    # plot commulative increase of eigenvalues
    plt.figure(figsize=(10, 10))
    # name of the plot
    plt.title("Commulative increase of eigenvalues")
    plt.plot(np.cumsum(sorted_eigvals))
    plt.xlabel("Index")
    plt.ylabel("Eigenvalue")
    plt.show()

    # number of connected components
    num_components = len([x for x in eigvals if np.isclose(x, 0, rtol=1e-10)])

    # fiedler vector is at num_components index in sorted_eigvals
    sorted_eigenvecs = eigvecs[:, np.argsort(eigvals)]
    fiedler_vec = sorted_eigenvecs[:, num_components]

    # plot sorted fiedler vector
    plt.figure(figsize=(10, 10))
    plt.title("Sorted fiedler vector")
    plt.plot(np.sort(fiedler_vec))
    plt.xlabel("Index")
    plt.ylabel("Fiedler vector")
    plt.show()

    cluster1 = []
    cluster2 = []
    for i in range(len(fiedler_vec)):
        if fiedler_vec[i] < 0:
            cluster1.append(i)
        else:
            cluster2.append(i)

    # number of connected components
    return num_components, cluster1, cluster2


def perform_louvain():
    '''
    Perform louvian algorithm
    '''

    contact_points = utils.get_contact_network(utils.read_file(Config.CONTACT_NET_FILE))

    # print(contact_points)

    # keys are the node labels
    # dict of nodes (node_label, node_index)
    n = len(contact_points)
    print("Number of nodes: ", n)
    nodes = { int(node_label): i for i, node_label in enumerate(contact_points.keys()) }


    # adjacency list
    adj_list = [[] for _ in range(len(nodes))]
    for node_label, node_ct_pts in contact_points.items():
        for ct_pt in node_ct_pts:
            adj_list[nodes[int(node_label)]].append(nodes[ct_pt.sibling_cp_id])

    G = nx.Graph()
    for i in range(len(adj_list)):
        for j in adj_list[i]:
            G.add_edge(i, j)

    # using networkx
    partition = community.louvain_communities(G)

    # make the value of nodes dict as key and key as value
    nodes = {v: k for k, v in nodes.items()}

    # write to file
    if os.path.exists(Config.COMM_DIR):
        shutil.rmtree(Config.COMM_DIR)
    os.makedirs(Config.COMM_DIR)
    
    comm_no = 0
    for comm_no, c in enumerate(partition):
        # write to file for each community count.txt
        with open(Config.COMM_DIR + str(comm_no) + ".txt", "w") as f:
            f.write(str([nodes[x] for x in c]))

