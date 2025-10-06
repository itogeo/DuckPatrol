import geopandas as gpd
from shapely.ops import unary_union
from pyproj import CRS
import pandas as pd

# === Helper: auto-detect UTM CRS ===
def get_utm_crs(geom):
    centroid = geom.centroid
    lon, lat = centroid.x, centroid.y
    utm_zone = int((lon + 180) / 6) + 1
    epsg = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone
    return CRS.from_epsg(epsg)

# === 1️⃣ File paths ===
houses_fp = "/Users/ianvandusen/Desktop/Ito/repos/DuckPatrol/data/houses_within_1mile.geojson"
out_fp    = "/Users/ianvandusen/Desktop/Ito/repos/DuckPatrol/data/house_tiered_buffers.geojson"

print("📂 Loading houses...")
houses = gpd.read_file(houses_fp)

# === 2️⃣ Ensure CRS ===
if houses.crs is None:
    raise ValueError("Input houses layer must have a defined CRS (e.g., EPSG:4326).")

if houses.crs.to_epsg() != 4326:
    houses = houses.to_crs(4326)

# === 3️⃣ Auto-detect UTM zone ===
utm_crs = get_utm_crs(houses.unary_union)
print(f"🧭 Auto-detected UTM zone: {utm_crs.to_authority()}")

houses_utm = houses.to_crs(utm_crs)

# === 4️⃣ Create union of all houses ===
houses_union = unary_union(houses_utm.geometry)

# === 5️⃣ Create tiered buffers (in meters) ===
mile_to_m = 1609.34
tiers = {
    "buffer_0_15mi": houses_union.buffer(0.10 * mile_to_m),
    "buffer_0_25mi": houses_union.buffer(0.25 * mile_to_m)
}

# === 6️⃣ Combine into GeoDataFrame with tier labels ===
buffer_gdfs = []
for name, geom in tiers.items():
    buffer_gdfs.append(gpd.GeoDataFrame({"tier": [name]}, geometry=[geom], crs=utm_crs))

buffers = pd.concat(buffer_gdfs, ignore_index=True)
buffers = gpd.GeoDataFrame(buffers, geometry="geometry", crs=utm_crs)

# === 7️⃣ Save as GeoJSON (WGS84) ===
buffers = buffers.to_crs(4326)
buffers.to_file(out_fp, driver="GeoJSON")

print(f"✅ Saved tiered house buffers → {out_fp}")
