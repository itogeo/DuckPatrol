import geopandas as gpd
import requests
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.validation import make_valid

# === 1️⃣ Load and clean AOI ===
aoi = gpd.read_file("/Users/ianvandusen/Desktop/Ito/repos/DuckPatrol/raw_data/boundary/east_gally_vector.shp")
aoi = aoi.to_crs(4326)
aoi = aoi[~aoi.geometry.is_empty]
aoi["geometry"] = aoi["geometry"].apply(make_valid)
aoi_union = unary_union(aoi.geometry)

# === 2️⃣ Bounding box ===
minx, miny, maxx, maxy = aoi_union.bounds

# === 3️⃣ Build Overpass query (raw HTTP, bypass OSMnx) ===
query = f"""
[out:json][timeout:60];
(
  way["building"]({miny},{minx},{maxy},{maxx});
  relation["building"]({miny},{minx},{maxy},{maxx});
);
out geom;
"""

print("📦 Downloading OSM buildings directly from Overpass…")
response = requests.get("https://overpass-api.de/api/interpreter", params={"data": query})
response.raise_for_status()
data = response.json()

# === 4️⃣ Convert to GeoDataFrame ===
elements = [el for el in data["elements"] if "geometry" in el]
geoms = []
for el in elements:
    try:
        coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
        geoms.append(shape({"type": "Polygon", "coordinates": [coords]}))
    except Exception:
        continue

gdf = gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326")

# === 5️⃣ Clip to AOI ===
gdf_clipped = gpd.clip(gdf, aoi)

# === 6️⃣ Save ===
outpath = "/Users/ianvandusen/Desktop/Ito/repos/DuckPatrol/data/houses.geojson"
gdf_clipped.to_file(outpath, driver="GeoJSON")

print(f"✅ Saved {len(gdf_clipped)} buildings to {outpath}")
