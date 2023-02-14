import geopandas as gpd
from shapely.geometry import Point, Polygon

def get_borders(state):
    borders = gpd.read_file('./state_outlines/tl_2022_us_state')
    borders = borders.to_crs(epsg=4326)
    borders = borders[['NAME', 'geometry']]
    borders = borders.set_index('NAME')
    return borders.loc[state]

state_polygons = get_borders() 
print(state_polygons)

def in_state(coord, state_border_polygons):
    p = Point(coord[1], coord[0])
    for state in state_border_polygons:
        if state.contains(p):
            return True
    return False
