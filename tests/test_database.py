from database import DATABASE_BACKEND, SupabaseConnection


class FakeConnection:
    def __init__(self):
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query = query
        self.params = params
        return self


def test_database_backend_is_explicitly_supported():
    assert DATABASE_BACKEND in {"sqlite", "supabase"}


def test_supabase_adapter_maps_table_names_and_placeholders():
    fake = FakeConnection()
    adapter = SupabaseConnection(fake)
    adapter.execute(
        "SELECT id FROM warnings WHERE guild_id = ? AND user_id = ?",
        (123, 456),
    )
    assert fake.query == "SELECT id FROM public.mk_warnings WHERE guild_id = %s AND user_id = %s"
    assert fake.params == (123, 456)


def test_supabase_adapter_translates_insert_or_ignore():
    fake = FakeConnection()
    adapter = SupabaseConnection(fake)
    adapter.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (123,))
    assert fake.query == "INSERT INTO public.mk_guild_settings (guild_id) VALUES (%s) ON CONFLICT DO NOTHING"
    assert fake.params == (123,)


def test_supabase_adapter_converts_boolean_settings():
    fake = FakeConnection()
    adapter = SupabaseConnection(fake)
    adapter.execute(
        "UPDATE guild_settings SET welcome_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
        (0, 123),
    )
    assert fake.query.startswith("UPDATE public.mk_guild_settings SET welcome_enabled = %s")
    assert fake.params == (False, 123)
