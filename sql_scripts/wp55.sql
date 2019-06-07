CREATE OR REPLACE FUNCTION calculate_lucky_luke_killers(p_min_kill_count INT DEFAULT 3, p_max_time_between_kills INT DEFAULT 10)
    RETURNS TABLE
            (
                match_id    uuid,
                killer_name text,
                kill_count  INT
            )
AS
$$
DECLARE
    max_count     INT;
    current_count INT;
    epoch         INT;
    frag_time     timestamptz(3);
    r1            RECORD;
    r2            RECORD;
BEGIN
    FOR r1 IN (SELECT DISTINCT T.match_id, T.killer_name
               FROM match_frag T
               ORDER BY T.match_id, T.killer_name)
        LOOP
            match_id := r1.match_id;
            killer_name := r1.killer_name;
            frag_time := to_timestamp(0);
            max_count := 0;
            current_count := 0;
            FOR r2 IN (SELECT T.match_id, T.frag_time, T.killer_name, T.victim_name
                       FROM match_frag T
                       WHERE (T.killer_name = r1.killer_name)
                          OR (T.victim_name = r1.killer_name))
                LOOP
                    epoch = EXTRACT(EPOCH FROM (r2.frag_time - frag_time));
                    IF (frag_time = to_timestamp(0) OR
                        r2.killer_name = killer_name AND r2.victim_name IS NOT NULL AND
                        epoch <= p_max_time_between_kills)
                    THEN
                        current_count = current_count + 1;
                        frag_time = r2.frag_time;
                    ELSIF (r2.killer_name = killer_name AND r2.victim_name IS NOT NULL AND
                           epoch > p_max_time_between_kills)
                    THEN
                        IF (current_count >= p_min_kill_count AND current_count > max_count)
                        THEN
                            max_count := current_count;
                        END IF;
                        current_count := 0;
                        frag_time := to_timestamp(0);
                    END IF;
                END LOOP;
            IF max_count >= p_min_kill_count
            THEN
                kill_count := max_count;
                RETURN NEXT;
            END IF;
        END LOOP;
END;
$$ LANGUAGE plpgsql;