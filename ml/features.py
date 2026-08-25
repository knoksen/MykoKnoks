LEGACY_FEATURE_COLUMNS = [
    "elevation_m",
    "slope_deg",
    "grassland_fraction",
    "forest_edge_fraction",
    "soil_moisture_proxy",
    "ndvi",
    "temp_mean_7d",
    "temp_mean_21d",
    "precip_sum_7d",
    "precip_sum_21d",
    "relative_humidity_mean_7d",
]

V1_HABITAT_FEATURE_COLUMNS = [
    "open_land_score",
    "wetland_score",
    "forest_score",
    "substrate_moisture_score",
    "elevation_m",
    "slope_deg",
    "terrain_roughness_m",
]

V1_TEMPORAL_FEATURE_COLUMNS = [
    "air_temperature_c",
    "relative_humidity_pct",
    "precipitation_rate_mm_h",
    "antecedent_precip_24h_mm",
    "antecedent_precip_72h_mm",
    "antecedent_precip_168h_mm",
    "moisture_memory_index",
]

# Preserve the original baseline contract for older experiments.
FEATURE_COLUMNS = LEGACY_FEATURE_COLUMNS
TARGET_COLUMN = "present"
