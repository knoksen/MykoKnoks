CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS data_sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  organisation TEXT NOT NULL,
  endpoint TEXT,
  license TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS species (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scientific_name TEXT NOT NULL UNIQUE,
  vernacular_name TEXT,
  taxon_source TEXT,
  taxon_key TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS observations (
  id BIGSERIAL PRIMARY KEY,
  species_id UUID REFERENCES species(id),
  source TEXT NOT NULL,
  source_record_id TEXT,
  observed_at TIMESTAMPTZ,
  geom geometry(Point, 4326) NOT NULL,
  coordinate_uncertainty_m DOUBLE PRECISION,
  dataset_id TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(source, source_record_id)
);
CREATE INDEX IF NOT EXISTS observations_geom_gix ON observations USING GIST (geom);
CREATE INDEX IF NOT EXISTS observations_species_time_idx ON observations(species_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS env_features (
  h3 TEXT PRIMARY KEY,
  h3_resolution SMALLINT NOT NULL,
  geom geometry(Polygon, 4326),
  elevation_m REAL,
  terrain TEXT,
  slope_deg REAL,
  ar5_arealtype TEXT,
  dominant_tree_species TEXT,
  forest_volume_m3_ha REAL,
  loose_sediment_type TEXT,
  ndvi REAL,
  soil_moisture_proxy REAL,
  grassland_proxy REAL,
  forest_edge_proxy REAL,
  completeness REAL CHECK (completeness BETWEEN 0 AND 1),
  feature_version TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS env_features_geom_gix ON env_features USING GIST (geom);

CREATE TABLE IF NOT EXISTS env_feature_evidence (
  h3 TEXT NOT NULL,
  source_id TEXT NOT NULL,
  acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_layer TEXT,
  payload JSONB,
  quality JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (h3, source_id, acquired_at)
);
CREATE INDEX IF NOT EXISTS env_feature_evidence_h3_idx ON env_feature_evidence(h3);

CREATE TABLE IF NOT EXISTS weather_features (
  h3 TEXT NOT NULL,
  valid_time TIMESTAMPTZ NOT NULL,
  source TEXT NOT NULL,
  air_temperature_c REAL,
  relative_humidity_pct REAL,
  precipitation_1h_mm REAL,
  precipitation_24h_mm REAL,
  precipitation_7d_mm REAL,
  growing_degree_days REAL,
  wind_speed_mps REAL,
  PRIMARY KEY (h3, valid_time, source)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline TEXT NOT NULL,
  status TEXT NOT NULL,
  area JSONB,
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  rows_written BIGINT NOT NULL DEFAULT 0,
  error TEXT
);

CREATE TABLE IF NOT EXISTS model_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  species_id UUID REFERENCES species(id),
  model_type TEXT NOT NULL,
  model_version TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  training_config JSONB NOT NULL,
  metrics JSONB NOT NULL,
  artifact_uri TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS predictions (
  h3 TEXT NOT NULL,
  species_id UUID REFERENCES species(id),
  valid_time TIMESTAMPTZ NOT NULL,
  habitat_score REAL NOT NULL CHECK (habitat_score BETWEEN 0 AND 1),
  fruiting_score REAL NOT NULL CHECK (fruiting_score BETWEEN 0 AND 1),
  combined_score REAL NOT NULL CHECK (combined_score BETWEEN 0 AND 1),
  confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  model_version TEXT NOT NULL,
  drivers JSONB,
  PRIMARY KEY (h3, species_id, valid_time, model_version)
);
