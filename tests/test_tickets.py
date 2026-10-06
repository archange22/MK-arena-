import pytest
from cogs.tickets import TICKET_TYPES, TicketPanelView, TicketControlView, INSCRIPTION_TEMPLATE
from bot.client import ChachaBot

def test_ticket_types_configured():
    assert "inscription" in TICKET_TYPES
    assert "staff" in TICKET_TYPES
    assert "clan" in TICKET_TYPES
    assert "support" in TICKET_TYPES
    for key, data in TICKET_TYPES.items():
        assert "label" in data
        assert "channel_prefix" in data
    assert "INSCRIPTION DE L’ÉQUIPE" in INSCRIPTION_TEMPLATE

def test_ticket_views():
    panel_view = TicketPanelView()
    assert len(panel_view.children) == 1
    assert panel_view.children[0].custom_id == "mk:ticket:select"

    control_view = TicketControlView()
    assert len(control_view.children) == 1
    assert control_view.children[0].custom_id == "mk:ticket:close"

@pytest.mark.asyncio
async def test_cogs_loading():
    bot = ChachaBot()
    await bot.load_extension("cogs.general")
    await bot.load_extension("cogs.tickets")
    
    assert "General" in bot.cogs
    assert "Tickets" in bot.cogs
    
    commands_names = [c.name for c in bot.commands]
    assert "ping" in commands_names
    assert "aide" in commands_names
    assert "ticket-setup" in commands_names
    assert "close" in commands_names
