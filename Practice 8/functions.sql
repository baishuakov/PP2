-- 3. Search (У друга называется search_contacts)
CREATE OR REPLACE FUNCTION search_contacts(p_pattern VARCHAR)
RETURNS TABLE(id INT, first_name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT c.id, c.first_name, c.phone FROM phonebook c
                 WHERE c.first_name ILIKE '%' || p_pattern || '%'
                    OR c.phone ILIKE '%' || p_pattern || '%';
END;
$$ LANGUAGE plpgsql;

-- 4. Pagination (У друга называется get_contacts_paginated)
CREATE OR REPLACE FUNCTION get_contacts_paginated(p_limit INT, p_offset INT)
RETURNS TABLE(id INT, first_name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT c.id, c.first_name, c.phone FROM phonebook c
                 ORDER BY c.id LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;