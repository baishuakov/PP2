from connect import get_connection

def run_phonebook():
    conn = get_connection()
    if conn is None: return
    cur = conn.cursor()

    try:
        # Теперь это сработает, так как в базе теперь TEXT
        cur.execute("CALL upsert_contact(%s, %s)", ("Messi", "+7777777"))

        names = ["Neymar", "Suarez", "Maga"]
        phones = ["+7771111", "+70577799", "123"]
        cur.execute("CALL bulk_insert_contacts(%s, %s, %s)", (names, phones, []))
        
        result = cur.fetchone()
        errors = result[0] if result else []
        if errors:
            print(f"Errors: {errors}")

        # Функции
        cur.execute("SELECT * FROM get_contacts_by_pattern(%s)", ("Messi",))
        print("Search results:", cur.fetchall())

        cur.execute("SELECT * FROM get_contacts_paged(%s, %s)", (2, 0))
        print("Paged results:", cur.fetchall())

        # Удаление
        cur.execute("CALL delete_contact_proc(%s)", ("Suarez",))

        conn.commit()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_phonebook()