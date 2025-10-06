import geopandas as gpd
from shapely.ops import unary_union
from pyproj import CRS

def get_utm_crs(geom):
    """Return an appropriate UTM CRS for the centroid of a geometry."""
    centroid = geom.centroid
    lon, lat = centroid.x, centroid.y
    utm_zone = int((lon + 180) / 6) + 1
    hemisphere = "north" if lat >= 0 else "south"
    epsg = 32600 + utm_zone if hemisphere == "north" else 32700 + utm_zone
    return CRS.from_epsg(epsg)

# === 1️⃣ Load data ===
river_fp = "/Users/ianvandusen/Desktop/Ito/repos/DuckPatrol/raw_data/waterways/east_gally/east_gallatin.gpkg"
houses_fp = "/Users/ianvandusen/Desktop/Ito/repos/DuckPatrol/data/houses.geojson"
out_fp = "/Users/ianvandusen/Desktop/Ito/repos/DuckPatrol/data/houses_within_1mile.geojson"

print("📂 Loading layers...")
rivers = gpd.read_file(river_fp)
houses = gpd.read_file(houses_fp)

# === 2️⃣ Detect & project to appropriate UTM zone ===
if rivers.crs is None:
    raise ValueError("River file has no CRS defined! Please set one (e.g., EPSG:4326).")

if rivers.crs.to_epsg() != 4326:
    rivers = rivers.to_crs(4326)
    houses = houses.to_crs(4326)

utm_crs = get_utm_crs(rivers.unary_union)
print(f"🧭 Auto-detected UTM zone: {utm_crs.to_authority()}")
rivers_utm = rivers.to_crs(utm_crs)
houses_utm = houses.to_crs(utm_crs)

# === 3️⃣ Buffer the river by 1 mile (1609.34 meters) ===
print("💧 Buffering river by 1 mile...")
river_union = unary_union(rivers_utm.geometry)
river_buffer = gpd.GeoDataFrame(geometry=[river_union.buffer(1609.34)], crs=utm_crs)

# === 4️⃣ Clip houses to buffer ===
print("🏠 Clipping houses to river buffer...")
houses_clipped = gpd.clip(houses_utm, river_buffer)

# === 5️⃣ Save output ===
houses_clipped = houses_clipped.to_crs(4326)  # Back to WGS84 for Leaflet/GeoJSON
houses_clipped.to_file(out_fp, driver="GeoJSON")
print(f"✅ Saved {len(houses_clipped)} houses within 1 mile of rivers to {out_fp}")
