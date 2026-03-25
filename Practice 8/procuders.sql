CREATE OR REPLACE PROCEDURE upsert_contact(p_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM phonebook WHERE first_name = p_name) THEN
        UPDATE phonebook SET phone = p_phone WHERE first_name = p_name;
    ELSE
        INSERT INTO phonebook(first_name, phone) VALUES(p_name, p_phone);
    END IF;
END;
$$;

-- 2. Bulk Insert
CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_names VARCHAR[], p_phones VARCHAR[], INOUT p_errors TEXT[] DEFAULT '{}'
)
LANGUAGE plpgsql AS $$
DECLARE i INT;
BEGIN
    FOR i IN 1 .. array_length(p_names, 1) LOOP
        IF p_phones[i] ~ '^[0-9+]+$' AND length(p_phones[i]) >= 7 THEN
            CALL upsert_contact(p_names[i], p_phones[i]);
        ELSE
            p_errors := array_append(p_errors, 'Invalid: ' || p_names[i]);
        END IF;
    END LOOP;
END;
$$;