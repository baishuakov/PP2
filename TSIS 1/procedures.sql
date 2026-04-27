-- =============================================================
-- procedures.sql  –  PL/pgSQL stored procedures & functions
-- =============================================================

-- ── 1. add_phone ──────────────────────────────────────────────
-- Adds a phone number to an existing contact (looked up by name).
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR   -- 'home' | 'work' | 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  name = p_contact_name
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Use home, work, or mobile.', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Phone % (%) added to contact "%".', p_phone, p_type, p_contact_name;
END;
$$;


-- ── 2. move_to_group ─────────────────────────────────────────
-- Moves a contact to a group; creates the group if it doesn't exist.
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  name = p_contact_name
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Get or create group
    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name)
        RETURNING id INTO v_group_id;
        RAISE NOTICE 'Group "%" created.', p_group_name;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;

    RAISE NOTICE 'Contact "%" moved to group "%".', p_contact_name, p_group_name;
END;
$$;


-- ── 3. search_contacts ───────────────────────────────────────
-- Searches contacts by name, email, or any phone number.
-- Returns distinct contacts matching the query pattern.
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id         INTEGER,
    name       VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phones     TEXT
)
LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_pattern TEXT := '%' || lower(p_query) || '%';
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name                                          AS group_name,
        string_agg(p.phone || ' (' || p.type || ')', ', '
                   ORDER BY p.type)                    AS phones
    FROM   contacts c
    LEFT JOIN groups g  ON g.id  = c.group_id
    LEFT JOIN phones p  ON p.contact_id = c.id
    WHERE  lower(c.name::text)  LIKE v_pattern
        OR lower(c.email::text) LIKE v_pattern
        OR lower(p.phone::text) LIKE v_pattern
    GROUP BY c.id, c.name, c.email, c.birthday, g.name
    ORDER BY c.name;
END;
$$;
