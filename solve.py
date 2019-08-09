"""
Read the data stored
Read the data sent
Create formulation
Run the solve!!!
Create output
"""
import json
import pickle
from math import ceil, floor
from collections import defaultdict

import pulp


def read_store():
    with open("q_tree.pkl", 'rb') as tree_in:
        q_tree = pickle.load(tree_in)
    with open("array.pkl", 'rb') as array_in:
        array_data = pickle.load(array_in)
    with open("attrs.pkl", 'rb') as attrs_in:
        attr_index = pickle.load(attrs_in)

    return q_tree, array_data, attr_index


def read_request():
    with open("mock_input.json", 'r') as inputd:
        return json.load(inputd)


def find_in_range(array_data, array_index, distance):
    steps = distance // 100
    loc_data = []
    for i in range(max(array_index[0] - steps, 0), min(array_index[0] + steps, array_data.shape[0])):
        for j in range(max(array_index[1] - steps, 0), min(array_index[1] + steps, array_data.shape[1])):
            loc_data.append(array_data[i][j][array_index[2]])

    return sum(loc_data)


def query_input_point(q_tree, location):
    return q_tree.query([location[0], location[1], location[0], location[1]])


def find_i_j(array_data, inter_query):
    i_index = (ceil(inter_query[1]/array_data.shape[0] - floor(inter_query[1]/array_data.shape[0])) * 125) - 1
    j_index = ceil(inter_query[1]/array_data.shape[0]) - 1
    
    return i_index, j_index


def parse_input_params(request_data, q_tree, array_data, attr_index):
    formulation_input = {}
    flip_attr = {v: k for k, v in attr_index.items()}

    for i, s in enumerate(request_data["sites"]):
        data = {
            "coord": s,
        }

        inter_query = query_input_point(q_tree, s)
        i_index, j_index = find_i_j(array_data, inter_query)


        metrics = request_data["metrics"][i]

        for m in metrics:
            if m in attr_index.values():
                k_index = flip_attr[m]
                data[m] = metrics[m]["value"] * find_in_range(
                    array_data,
                    [i_index, j_index, k_index],
                    metrics[m]["distance"]
                )
            else:
                data[m] = metrics[m]["value"]
        formulation_input[i] = data

    return [
        formulation_input,
        request_data.get("out_count", 1),
        request_data.get("budget", 0),
    ]


def create_formulation(f_input_data):
    input_vars = f_input_data[0]
    sites = f_input_data[1]
    budget = f_input_data[2]

    solver = pulp.solvers.COIN()

    mdl_vars = {}

    for k, v in input_vars.items():
        mdl_vars[k] = pulp.LpVariable(f"x{k}", 0, 1, cat='Integer')

    prob = pulp.LpProblem("problem", pulp.LpMinimize)

    ## Create objective to minimize total cost by adding all the things

    objective = []
    obj_list = [cost*mdl_vars[k] for k, w_cost in input_vars.items() for t_cost, cost in w_cost.items() if t_cost != "coord"]
    prob += pulp.lpSum(obj_list)

    ## Create constraints to choose the constrained number of sites

    lhs = pulp.LpAffineExpression((mdl_vars[k], 1) for k in mdl_vars.keys())
    rhs = sites
    prob += (lhs >= rhs)

    ## Create budget constraints
    if budget:
        lhs = pulp.LpAffineExpression((mdl_vars[k], input_vars[k]["cost"]) for k in mdl_vars.keys())
        rhs = budget 
        prob += (lhs <= rhs)

    prob.writeLP("test.lp")
    status = prob.solve()


    solution = []
    for k in mdl_vars:
        value = pulp.value(mdl_vars[k])
        if value:
            solution.append(k)

    return solution


def create_response(solution, f_data, request, attr_index):
    out_solution = {
      "type": "FeatureCollection",
      "features": [
      ]
    }
    for i, in_point in enumerate(request['sites']):

        properties = {}
        if i in solution:
            properties["solution"] = 1
        else:
            properties["solution"] = 0

        for k, v in attr_index.items():
            
            properties[v] = f_data[0][i].get(v, 0) / request["metrics"][i].get(v, {"value": 1})["value"]

        a_feature = {
            "type": "Feature",
            "geometry": {
            "type": "Point",
                "coordinates": request["sites"][i]
            },
            "properties": properties
        }

        out_solution["features"].append(a_feature)

    return out_solution




def run(request):
    q_tree, array_data, attr_index = read_store()

    # request = read_request() run on local save data
    f_data = parse_input_params(
        request.json,
        q_tree,
        array_data,
        attr_index
    )
    solution = create_formulation(f_data)

    return json.dumps(create_response(
        solution,
        f_data,
        request,
        attr_index
    ))
