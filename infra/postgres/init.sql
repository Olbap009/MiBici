CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    departures_prev_30m INTEGER NOT NULL,
    arrivals_prev_30m INTEGER NOT NULL,
    departures_prev_2h INTEGER NOT NULL,
    arrivals_prev_2h INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    prediction TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_class ON predictions (prediction);
