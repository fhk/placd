"""
Scrape the data and create the array
"""

GRIDS = "/home/plantz/grid.shp"
ADDRESSES = "/home/plantz/Downloads/sf_adds.shp"
POIS = "/home/plantz/Downloads/norcal-latest-free.shp/gis_osm_pois_a_free_1.shp"
STREETS = "/home/plantz/Downloads/norcal-latest-free.shp/gis_osm_roads_free_1.shp"


from math import floor, ceil
import numpy as np
import geopandas as gpd
from scipy import spatial
import pickle

def poi_data(q_tree, input_array, polys):
    pois = gpd.read_file(POIS)

    all_of_them = {i: k for i, k in enumerate(set(pois['fclass'].values))}
    count = 0

    for k, v in all_of_them.items():
        print(v)
        which_ones = pois[pois["fclass"] == v]

        for index, one in which_ones.iterrows():

            geom = one.geometry
            
            if geom.geom_type in ["Polygon", "MultiPolygon"]:
                if geom.geom_type == "MultiPolygon":
                    coords = geom[0].exterior.coords[:]
                else:
                    coords = geom.exterior.coords[:]
                # hack to get a small polygon
                result = q_tree.query(
                    [coords[0][0], coords[0][1],
                    coords[1][0], coords[1][1]],
                    k=1
                )

                if polys.iloc[result[1]].geometry.intersects(geom):
                    count += 1
                    i_index = (ceil(result[1]/input_array.shape[0] - floor(result[1]/input_array.shape[0])) * input_array.shape[0]) - 1
                    j_index = ceil(result[1]/input_array.shape[0]) - 1
                    input_array[i_index][j_index][k] = input_array[i_index][j_index][k] + 1

            else:
                print(geom.geom_type)
    print(f"found {count} pois in SF")



    return all_of_them


def add_population_data(input_array, dim_index, g_df):
    add_df = gpd.read_file(ADDRESSES)
    q_tree_adds = []

    for g in add_df["geometry"]:
        coords = g.coords[0]
        q_tree_adds.append([coords[0], coords[1], coords[0], coords[1]])

    add_tree = spatial.cKDTree(q_tree_adds)

    for i, g in enumerate(g_df["geometry"]):
        p_coords = g.centroid.coords[0]
        poly = [p_coords[0], p_coords[1], p_coords[0], p_coords[1]]        
        # print(len(add_tree.query_ball_point(poly, r=0.002)))

            





def write_quad_n_array_plus_index(q_tree, array_data, attr_index):
    with open("q_tree.pkl", "wb") as tree_out:
        pickle.dump(q_tree, tree_out)
    with open("array.pkl", "wb") as array_out:
        pickle.dump(array_data, array_out)
    with open("attrs.pkl", "wb") as attrs_out:
        pickle.dump(attr_index, attrs_out)

def main():
    g_df = gpd.read_file(GRIDS)

    q_tree_corners = []

    for i, f in enumerate(g_df.geometry):
        coords = list(f.exterior.coords)
        q_tree_corners.append([coords[0][0], coords[0][1], coords[2][0], coords[2][1]])

    q_tree = spatial.cKDTree(q_tree_corners)

    # assuming we have 151 items in a row and 125 in a column
    array_data = np.zeros((125, 151, 126))

    attr_index = poi_data(q_tree, array_data, g_df)

    add_population_data(array_data, 125, g_df)

    write_quad_n_array_plus_index(q_tree, array_data, attr_index)


if __name__ == "__main__":
    main()
