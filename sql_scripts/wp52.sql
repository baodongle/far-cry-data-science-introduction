CREATE OR REPLACE FUNCTION get_killer_class(weapon_code text) RETURNS text AS
$$
BEGIN
    RETURN CASE
               WHEN weapon_code IN ('Machete', 'Falcon', 'MP5') THEN 'Hitman'
               WHEN weapon_code = 'SniperRifle' THEN 'Sniper'
               WHEN weapon_code IN
                    ('AG36', 'OICW', 'P90', 'M4', 'Shotgun', 'M249')
                   THEN 'Commando'
               WHEN weapon_code IN
                    ('Rocket', 'VehicleRocket', 'HandGrenade',
                     'StickExplosive', 'Boat', 'Vehicle',
                     'VehicleMountedRocketMG', 'VehicleMountedAutoMG', 'MG',
                     'VehicleMountedMG', 'OICWGrenade',
                     'AG36Grenade') THEN 'Psychopath'
               ELSE 'Other'
        END;
END;
$$ LANGUAGE plpgsql;

-- Determine Players Killer Class
SELECT match_id,
       player_name,
       weapon_code,
       kill_count,
       get_killer_class(weapon_code) AS killer_class
FROM (
         SELECT match_id,
                killer_name        AS player_name,
                weapon_code,
                count(weapon_code) AS kill_count,
                row_number() OVER (
                    PARTITION BY match_id, killer_name
                    ORDER BY count(weapon_code) DESC
                    )              AS pos
         FROM match_frag
         WHERE victim_name IS NOT NULL
         GROUP BY match_id, killer_name, weapon_code
         ORDER BY match_id, killer_name, kill_count DESC
     ) AS ss
WHERE pos = 1;