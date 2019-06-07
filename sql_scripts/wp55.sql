CREATE OR REPLACE FUNCTION calculate_lucky_luke_killers(p_min_kill_count int DEFAULT 3, p_max_time_between_kills int DEFAULT 10)
    RETURNS table
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
    row1          RECORD;
    row2          RECORD;
BEGIN
    FOR row1 IN (SELECT DISTINCT T.match_id, T.killer_name
                 FROM match_frag AS T
                 ORDER BY T.match_id, T.killer_name)
        LOOP
            match_id := row1.match_id;
            killer_name := row1.killer_name;
            max_count := 0;
            current_count := 0;
            FOR row2 IN (SELECT T2.match_id, T2.killer_name, T2.elasped_time
                         FROM (SELECT T.match_id,
                                      T.killer_name,
                                      extract(EPOCH FROM (T.frag_time - lag(T.frag_time, 1)
                                                                        OVER (PARTITION BY T.killer_name ORDER BY T.frag_time))) AS elasped_time
                               FROM match_frag AS T) AS T2
                         WHERE T2.elasped_time IS NOT NULL
                           AND row1.killer_name = T2.killer_name)
                LOOP
                    IF (row2.elasped_time <= p_max_time_between_kills)
                    THEN
                        current_count = current_count + 1;
                    ELSIF (row2.elasped_time > p_max_time_between_kills)
                    THEN
                        IF (max_count < current_count)
                        THEN
                            max_count := current_count;
                        END IF;
                        current_count := 0;
                    END IF;
                END LOOP;
            IF (max_count >= p_min_kill_count)
            THEN
                kill_count := max_count;
                RETURN NEXT;
            END IF;
        END LOOP;
END;
$$ LANGUAGE plpgsql;