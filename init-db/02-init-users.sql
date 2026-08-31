-- 02-init-users.sql
-- UDT-X Platform User & Settings Database Initialization

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'analyst', -- 'analyst' | 'admin'
    avatar_seed VARCHAR(100) DEFAULT 'enclave-operator',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    has_completed_tour BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings_json JSONB NOT NULL DEFAULT '{
        "alerting": {
            "sound_on_critical": true,
            "min_notification_severity": "high",
            "live_monitor_autoscroll": true
        },
        "display": {
            "density": "comfortable",
            "sphere_particle_density": "high",
            "default_time_range": "24h"
        },
        "data_export": {
            "default_format": "CEF"
        }
    }',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default initial station admin account (password: 'AdminEnclave2026!')
-- Password hash generated via bcrypt
INSERT INTO users (id, email, password_hash, display_name, role, avatar_seed, has_completed_tour)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'admin@udtx.local',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Station Commander',
    'admin',
    'commander',
    false
) ON CONFLICT (email) DO NOTHING;

INSERT INTO user_settings (user_id)
VALUES ('a0000000-0000-0000-0000-000000000001')
ON CONFLICT (user_id) DO NOTHING;
