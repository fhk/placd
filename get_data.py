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
    all_of_them = {
        0: "attraction",
        1: "restaurant",
        2: "supermarket",
        3: "cafe",
        4: "bank",
        5: "hotel",
    }

    pois = gpd.read_file(POIS)

    count = 0

    for k, v in all_of_them.items():
        print(v)
        which_ones = pois[pois["fclass"] == v]

        for index, one in which_ones.iterrows():

            geom = one.geometry
            
            if geom.geom_type == "Polygon":
                coords = geom.exterior.coords[:]
                # hack to get a small polygon
                result = q_tree.query(
                    [coords[0][0], coords[0][1],
                    coords[1][0], coords[1][1]],
                    k=1
                )

                if polys.iloc[result[1]].geometry.intersects(geom):
                    count += 1
                    i_index = (ceil(result[1]/input_array.shape[0] - floor(result[1]/array_data.shape[0])) * array_data.shape[0]) - 1
                    j_index = ceil(result[1]/input_array.shape[0]) - 1
                    input_array[i_index][j_index][k] = input_array[i_index][j_index][k] + 1

    print(f"found {count} pois in SF")

    return all_of_them


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

    q_tree = spatial.KDTree(q_tree_corners)

    # assuming we have 151 items in a row and 125 in a column
    array_data = np.zeros((125, 151, 6))

    attr_index = poi_data(q_tree, array_data, g_df)

    write_quad_n_array_plus_index(q_tree, array_data, attr_index)


if __name__ == "__main__":
    main()
