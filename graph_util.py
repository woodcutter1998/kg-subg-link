import numpy as np
import scipy.sparse as ssp
import torch
import dgl
import random


def sample_neg_link(adj, rel, head, tail, num_nodes, sample_size):
    arr = np.arange(num_nodes)
    cur_adj = adj[rel]
    neg_head_neighbor = cur_adj.col[cur_adj.row==head]
    neg_tail_neighbor = cur_adj.row[cur_adj.col==tail]
    cans = set(arr)
    tail_cans = cans.difference(neg_head_neighbor)
    tail_cans.discard(head)
    head_cans = cans.difference(neg_tail_neighbor)
    head_cans.discard(tail)
    tail_can_arr = np.array(list(tail_cans))
    head_can_arr = np.array(list(head_cans))
    # print(type(tail_can_arr))
    # print(tail_cans)
    tail_sample = np.random.choice(tail_can_arr, sample_size, replace = False)
    head_sample = np.random.choice(head_can_arr, sample_size, replace = False)
    neg_tail_links = [[head, rel, neg_tail] for neg_tail in tail_sample]
    neg_head_links = [[neg_head, rel, tail] for neg_head in head_sample]
    neg_links = neg_tail_links+neg_head_links
    neg_links = random.choices(neg_links, k=sample_size)
    return neg_links


def sample_filtered_neg_tail(adj, rel, head, tail, num_nodes, sample_size):
    arr = np.arange(num_nodes)
    cur_adj = adj[rel]
    neg_head_neighbor = cur_adj.col[cur_adj.row==head]
    cans = set(arr)
    cans.difference_update(neg_head_neighbor)
    cans.discard(tail)
    cans.discard(head)
    tail_can_list = list(cans)
    neg_tail_links = [[head, rel, neg_tail] for neg_tail in tail_can_list]
    return neg_tail_links

def sample_filtered_neg_head(adj, rel, head, tail, num_nodes, sample_size):
    arr = np.arange(num_nodes)
    cur_adj = adj[rel]
    neg_tail_neighbor = cur_adj.row[cur_adj.col==tail]
    cans = set(arr)
    cans.difference_update(neg_tail_neighbor)
    cans.discard(head)
    cans.discard(tail)
    head_can_list = list(cans)
    neg_head_links = [[neg_head, rel, tail] for neg_head in head_can_list]
    return neg_head_links

def sample_arb_neg(adj, rel, head, tail, num_nodes, sample_size):
    head = np.random.randint(num_nodes)
    arr = np.arange(num_nodes)
    cur_adj = adj[rel]
    neg_head_neighbor = cur_adj.col[cur_adj.row==head]
    cans = set(arr)
    cans.difference_update(neg_head_neighbor)
    cans.discard(head)
    tail_can_list = list(cans)
    tail_ind = np.random.randint(len(tail_can_list))
    return [[head,rel,tail_can_list[tail_ind]]]

def remove_nodes(A_incidence, nodes):
    idxs_wo_nodes = list(set(range(A_incidence.shape[1])) - set(nodes))
    return A_incidence[:, idxs_wo_nodes][idxs_wo_nodes, :]


def construct_graph_from_edges(edges, n_entities):
    g = dgl.graph((edges[0], edges[2]), num_nodes=n_entities)
    g.edata['type'] = torch.tensor(edges[1], dtype=torch.int32)
    g.edata['mask'] = torch.tensor(np.ones((len(edges[0]),1)), dtype=torch.int32)
    return g

def construct_homogeneous_graph_from_edges(edges, n_entities):
    g = dgl.graph((np.concatenate((edges[0],edges[2])), np.concatenate((edges[2],edges[0]))), num_nodes=n_entities)
    g.edata['type'] = torch.tensor(np.concatenate((edges[1],edges[1])), dtype=torch.int32)
    g.edata['mask'] = torch.tensor(np.ones((len(edges[0])*2,1)), dtype=torch.int32)
    return g

def construct_reverse_graph_from_edges(edges, n_entities, num_rel):
    g = dgl.graph((np.concatenate((edges[0],edges[2])), np.concatenate((edges[2],edges[0]))), num_nodes=n_entities)
    g.edata['type'] = torch.tensor(np.concatenate((edges[1],edges[1]+num_rel)), dtype=torch.int32)
    g.edata['mask'] = torch.tensor(np.ones((len(edges[0])*2,1)), dtype=torch.int32)
    return g

# def extract_neighbor_nodes(roots, adj, h=1, max_nodes_per_hop=None, median_mult=50000, inc_size=0):
#     cur_nodes = roots
#     visited = set()
#     in_hop_neighbor = []
#     # st = time.time()
#     sim_nodes=np.zeros(adj.shape[0])
#     visited.update(cur_nodes)
#     for i in range(h):
#         # print("sparse hop",i)
#         # st = time.time()
#         neighb = []
#         small_nodes = np.array(list(cur_nodes))
#         if len(small_nodes)==0:
#             break
#         # print("candidate", time.time()-st)
#         neighbor_count = adj.indptr[small_nodes+1] - adj.indptr[small_nodes]
#         neighbor_count_median = np.median(neighbor_count)
#         # print("median", time.time()-st)
#         for j, cur in enumerate(small_nodes):
#             if i>0 and neighbor_count[j]>neighbor_count_median*median_mult:
#                 continue
#             neighbors = adj.indices[adj.indptr[cur]: adj.indptr[cur+1]]
#             n_set = sim_nodes[neighbors]
#             n_num = len(n_set)
#             n_same_num = np.sum(n_set)
#             if i>0 and (n_same_num/n_num)<(i)*inc_size:
#                 continue
#             neighb.append(neighbors)
#         if len(neighb)==0:
#             break
#         # print("filter", time.time()-st)
#         neighbor_nodes = np.concatenate(neighb)
#         sz = len(neighbor_nodes)
#         neighbor_nodes, counts = np.unique(neighbor_nodes, return_counts=True)
#         sim_nodes = np.zeros(adj.shape[0])
#         sim_nodes[neighbor_nodes] = 1
#         # print("sim dict",time.time()-st)
#         if max_nodes_per_hop and max_nodes_per_hop<len(neighbor_nodes):
#             next_nodes = np.random.choice(neighbor_nodes, max_nodes_per_hop, p=counts/sz)
#             next_nodes = set(next_nodes)
#         else:
#             next_nodes = set(neighbor_nodes)
#         next_nodes.difference_update(visited)
#         visited.update(next_nodes)
#         in_hop_neighbor.append(next_nodes)
#         cur_nodes = next_nodes
#         # print("update",time.time()-st)
#     return set().union(*in_hop_neighbor)


def extract_neighbor_nodes(roots, adj, h=1, max_nodes_per_hop=None):
    cur_nodes = roots
    visited = set()
    in_hop_neighbor = []
    # st = time.time()
    visited.update(cur_nodes)
    for i in range(h):
        # print("sparse hop",i)
        # st = time.time()
        neighb = []
        small_nodes = np.array(list(cur_nodes))
        if len(small_nodes)==0:
            break
        for j, cur in enumerate(small_nodes):
            neighbors = adj.indices[adj.indptr[cur]: adj.indptr[cur+1]]
            neighb.append(neighbors)
        if len(neighb)==0:
            break
        # print("filter", time.time()-st)
        neighbor_nodes = np.concatenate(neighb)
        sz = len(neighbor_nodes)
        neighbor_nodes, counts = np.unique(neighbor_nodes, return_counts=True)
        # print("sim dict",time.time()-st)
        if max_nodes_per_hop and max_nodes_per_hop<len(neighbor_nodes):
            next_nodes = np.random.choice(neighbor_nodes, max_nodes_per_hop, p=counts/sz)
            next_nodes = set(next_nodes)
        else:
            next_nodes = set(neighbor_nodes)
        next_nodes.difference_update(visited)
        visited.update(next_nodes)
        in_hop_neighbor.append(next_nodes)
        cur_nodes = next_nodes
        # print("update",time.time()-st)
    return set().union(*in_hop_neighbor)


# def get_neighbor_nodes(roots, adj, h=1, max_nodes_per_hop=None):
#     cur_nodes = roots
#     visited = set()
#     in_hop_neighbor = []
#     inc_size = 0
#     # st = time.time()
#     if isinstance(adj, np.ndarray):
#         visited.update(cur_nodes)
#         for i in range(h):
#             # print("dense hop:",i)
#             # st = time.time()
#             small_nodes = np.array(list(cur_nodes))
#             # print("create candidiate", time.time()-st)
#             if len(small_nodes)==0:
#                 break
#             if i>0:
#                 neighbor_sim = np.sum(np.logical_and(adj[small_nodes], sim_dict),axis=-1)
#                 neighbor_count = np.sum(adj[small_nodes], axis=-1)
#                 neighbor_count_median = np.median(neighbor_count)
#                 small_nodes = small_nodes[np.logical_and(neighbor_count<neighbor_count_median*500000,neighbor_sim/neighbor_count>=inc_size*(i-1))]
#                 # small_nodes = small_nodes[neighbor_count<neighbor_count_median*1.5]
#             if len(small_nodes)==0:
#                 break
#             # print("filter", time.time()-st)
#             neighbor_nodes = adj[small_nodes, :].nonzero()[1]
#             sz = len(neighbor_nodes)
#             neighbor_nodes, counts = np.unique(neighbor_nodes, return_counts=True)
#             sim_dict = np.zeros(len(adj))
#             sim_dict[neighbor_nodes] = 1
#             # print("create dict", time.time()-st)
#             if max_nodes_per_hop and max_nodes_per_hop<len(neighbor_nodes):
#                 next_nodes = np.random.choice(neighbor_nodes, max_nodes_per_hop, p=counts/sz)
#                 next_nodes = set(next_nodes)
#             else:
#                 next_nodes = set(neighbor_nodes)
#             next_nodes.difference_update(visited)
#             visited.update(next_nodes)
#             in_hop_neighbor.append(next_nodes)
#             cur_nodes = next_nodes
#             # print("update", time.time()-st)
#     else:
#         sim_nodes=np.zeros(adj.shape[0])
#         visited.update(cur_nodes)
#         for i in range(h):
#             # print("sparse hop",i)
#             # st = time.time()
#             neighb = []
#             small_nodes = np.array(list(cur_nodes))
#             if len(small_nodes)==0:
#                 break
#             # print("candidate", time.time()-st)
#             neighbor_count = adj.indptr[small_nodes+1] - adj.indptr[small_nodes]
#             neighbor_count_median = np.median(neighbor_count)
#             # print("median", time.time()-st)
#             for j, cur in enumerate(small_nodes):
#                 if i>0 and neighbor_count[j]>neighbor_count_median*50000:
#                     continue
#                 neighbors = adj.indices[adj.indptr[cur]: adj.indptr[cur+1]]
#                 n_set = sim_nodes[neighbors]
#                 n_num = len(n_set)
#                 n_same_num = np.sum(n_set)
#                 if i>0 and (n_same_num/n_num)<(i-1)*inc_size:
#                     continue
#                 neighb.append(neighbors)
#             if len(neighb)==0:
#                 break
#             # print("filter", time.time()-st)
#             neighbor_nodes = np.concatenate(neighb)
#             sz = len(neighbor_nodes)
#             neighbor_nodes, counts = np.unique(neighbor_nodes, return_counts=True)
#             sim_nodes = np.zeros(adj.shape[0])
#             sim_nodes[neighbor_nodes] = 1
#             # print("sim dict",time.time()-st)
#             if max_nodes_per_hop and max_nodes_per_hop<len(neighbor_nodes):
#                 next_nodes = np.random.choice(neighbor_nodes, max_nodes_per_hop, p=counts/sz)
#                 next_nodes = set(next_nodes)
#             else:
#                 next_nodes = set(neighbor_nodes)
#             next_nodes.difference_update(visited)
#             visited.update(next_nodes)
#             in_hop_neighbor.append(next_nodes)
#             cur_nodes = next_nodes
#             # print("update",time.time()-st)
#     return set().union(*in_hop_neighbor)


def get_neighbor_nodes(roots, adj, h=1, max_nodes_per_hop=None):
    cur_nodes = roots
    visited = set()
    in_hop_neighbor = []
    visited.update(cur_nodes)
    for i in range(h):
        small_nodes = np.array(list(cur_nodes))
        if len(small_nodes)==0:
            break
        neighbor_nodes = adj[small_nodes, :].nonzero()[1]
        sz = len(neighbor_nodes)
        neighbor_nodes, counts = np.unique(neighbor_nodes, return_counts=True)
        # print("create dict", time.time()-st)
        if max_nodes_per_hop and max_nodes_per_hop<len(neighbor_nodes):
            next_nodes = np.random.choice(neighbor_nodes, max_nodes_per_hop, p=counts/sz)
            next_nodes = set(next_nodes)
        else:
            next_nodes = set(neighbor_nodes)
        next_nodes.difference_update(visited)
        visited.update(next_nodes)
        in_hop_neighbor.append(next_nodes)
        cur_nodes = next_nodes
        # print("update", time.time()-st)
    return set().union(*in_hop_neighbor)

def node_label(subgraph, max_distance=1):
    # implementation of the node labeling scheme described in the paper
    roots = [0, 1]
    root_dist = np.clip(ssp.csgraph.dijkstra(subgraph, indices=[0], directed=False, unweighted=True, limit=1e2)[:, 1], 0, 1e7)
    sgs_single_root = [remove_nodes(subgraph, [root]) for root in roots]
    dist_to_roots = [np.clip(ssp.csgraph.dijkstra(sg, indices=[0], directed=False, unweighted=True, limit=1e6)[:, 1:], 0, 1e7) for r, sg in enumerate(sgs_single_root)]
    dist_to_roots = np.array(list(zip(dist_to_roots[0][0], dist_to_roots[1][0])), dtype=int)
    target_node_labels = np.array([[0, 1], [1, 0]])
    labels = np.concatenate((target_node_labels, dist_to_roots)) if dist_to_roots.size else target_node_labels
    # print(labels[np.where(np.logical_and(labels[:,0]>2*max_distance, labels[:,1]>2*max_distance)>0)[0]])
    # print(labels)
    labels[labels>2*max_distance]=9
    # enclosing_subgraph_nodes = np.where(np.logical_and(np.max(labels, axis=1) <= max_distance))[0]
    enclosing_subgraph_nodes = np.where(labels[:,0]+labels[:,1]<=max_distance+1)[0]
    # print(enclosing_subgraph_nodes)
    # disconnected_subgraph_nodes = np.where(np.logical_and(np.min(labels, axis=1) > max_distance,np.max(labels, axis=1) <= 2* max_distance))[0]
    disconnected_subgraph_nodes = np.where(np.max(labels, axis=1) > 2* max_distance)[0]
    # print(disconnected_subgraph_nodes)
    return labels, enclosing_subgraph_nodes, disconnected_subgraph_nodes, root_dist[0]


# def node_label(subgraph, max_distance=1):
#     # implementation of the node labeling scheme described in the paper
#     roots = [0, 1]
#     sgs_single_root = [remove_nodes(subgraph, [root]) for root in roots]
#     dist_to_roots = [np.clip(ssp.csgraph.dijkstra(sg, indices=[0], directed=False, unweighted=True, limit=1e3)[:, 1:], 0, 2*max_distance+1) for r, sg in enumerate(sgs_single_root)]
#     dist_to_roots = np.array(list(zip(dist_to_roots[0][0], dist_to_roots[1][0])), dtype=int)
#     target_node_labels = np.array([[0, 1], [1, 0]])
#     labels = np.concatenate((target_node_labels, dist_to_roots)) if dist_to_roots.size else target_node_labels
    
#     enclosing_subgraph_nodes = np.where(np.max(labels, axis=1) <= 2* max_distance+1)[0]
#     # print(disconnected_subgraph_nodes)
#     return labels, enclosing_subgraph_nodes, None, 0



def subgraph_extraction_labeling_wiki(ind, rel, A_incidence, h=1, enclosing_sub_graph=False, max_nodes_per_hop=None, max_node_label_value=None):
    # extract the h-hop enclosing subgraphs around link 'ind'
    root1_nei = get_neighbor_nodes(set([ind[0]]), A_incidence, h, max_nodes_per_hop)
    root2_nei = get_neighbor_nodes(set([ind[1]]), A_incidence, h, max_nodes_per_hop)

    subgraph_nei_nodes_int = root1_nei.intersection(root2_nei)
    subgraph_nei_nodes_un = root1_nei.union(root2_nei)
    # print(subgraph_nei_nodes_int)
    # print(subgraph_nei_nodes_un)

    # Extract subgraph | Roots being in the front is essential for labelling and the model to work properly.
    if enclosing_sub_graph:
        subgraph_nodes = list(ind) + list(subgraph_nei_nodes_int)
    else:
        subgraph_nodes = list(ind) + list(subgraph_nei_nodes_un)

    labels, enclosing_subgraph_nodes, disconnected_nodes, root_dist = node_label(A_incidence[subgraph_nodes, :][:, subgraph_nodes], max_distance=h)


    return subgraph_nodes, labels, enclosing_subgraph_nodes, disconnected_nodes, root_dist

