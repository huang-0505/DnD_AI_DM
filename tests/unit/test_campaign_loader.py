"""
Unit tests for orchestrator/campaign_loader.py
Tests CampaignLoader and CampaignTemplate classes.
"""

import pytest
import sys
from pathlib import Path

# Add orchestrator to path
ORCHESTRATOR_PATH = Path(__file__).parent.parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_PATH))

from campaign_loader import CampaignLoader, CampaignTemplate, CAMPAIGNS


@pytest.mark.unit
class TestCampaignTemplate:
    """Test CampaignTemplate class functionality."""

    def test_template_initialization(self):
        """Test creating a campaign template."""
        template = CampaignTemplate(
            id="test-campaign",
            name="Test Campaign",
            description="A test campaign",
            opening_narrative="You begin your adventure...",
            starting_location="Test Location"
        )
        
        assert template.id == "test-campaign"
        assert template.name == "Test Campaign"
        assert template.description == "A test campaign"
        assert template.opening_narrative == "You begin your adventure..."
        assert template.starting_location == "Test Location"
        assert template.initial_quest is None
        assert template.difficulty == "medium"

    def test_template_with_optional_fields(self):
        """Test creating template with all optional fields."""
        template = CampaignTemplate(
            id="test",
            name="Test",
            description="Test",
            opening_narrative="Test",
            starting_location="Test",
            initial_quest="Find the treasure",
            difficulty="hard"
        )
        
        assert template.initial_quest == "Find the treasure"
        assert template.difficulty == "hard"

    def test_template_to_dict(self):
        """Test converting template to dictionary."""
        template = CampaignTemplate(
            id="test",
            name="Test Campaign",
            description="Test desc",
            opening_narrative="Test narrative",
            starting_location="Test Location",
            initial_quest="Test quest",
            difficulty="easy"
        )
        
        template_dict = template.to_dict()
        assert template_dict["id"] == "test"
        assert template_dict["name"] == "Test Campaign"
        assert template_dict["description"] == "Test desc"
        assert template_dict["opening_narrative"] == "Test narrative"
        assert template_dict["starting_location"] == "Test Location"
        assert template_dict["initial_quest"] == "Test quest"
        assert template_dict["difficulty"] == "easy"


@pytest.mark.unit
class TestCampaignLoader:
    """Test CampaignLoader class functionality."""

    def test_list_campaigns(self):
        """Test listing all available campaigns."""
        campaigns = CampaignLoader.list_campaigns()
        
        assert isinstance(campaigns, list)
        assert len(campaigns) > 0
        # Should include predefined campaigns
        campaign_ids = [c["id"] for c in campaigns]
        assert "stormwreck-isle" in campaign_ids or "classic-dungeon" in campaign_ids

    def test_list_campaigns_structure(self):
        """Test campaign list structure."""
        campaigns = CampaignLoader.list_campaigns()
        
        if len(campaigns) > 0:
            campaign = campaigns[0]
            assert "id" in campaign
            assert "name" in campaign
            assert "description" in campaign
            assert "opening_narrative" in campaign
            assert "starting_location" in campaign

    def test_get_campaign_existing(self):
        """Test getting an existing campaign."""
        campaign = CampaignLoader.get_campaign("stormwreck-isle")
        
        if campaign:
            assert campaign.id == "stormwreck-isle"
            assert campaign.name is not None
            assert campaign.opening_narrative is not None

    def test_get_campaign_nonexistent(self):
        """Test getting a non-existent campaign returns None."""
        campaign = CampaignLoader.get_campaign("nonexistent-campaign")
        assert campaign is None

    def test_initialize_campaign_basic(self):
        """Test initializing a campaign without character customization."""
        result = CampaignLoader.initialize_campaign("stormwreck-isle")
        
        assert result["campaign_id"] == "stormwreck-isle"
        assert "campaign_name" in result
        assert "initial_prompt" in result
        assert "starting_location" in result
        assert "initial_quest" in result
        assert "metadata" in result

    def test_initialize_campaign_with_character_class(self):
        """Test initializing campaign with character class."""
        result = CampaignLoader.initialize_campaign(
            "stormwreck-isle",
            character_class="Fighter"
        )
        
        assert result["campaign_id"] == "stormwreck-isle"
        assert result["metadata"]["character_class"] == "Fighter"
        assert "Fighter" in result["initial_prompt"] or "fighter" in result["initial_prompt"].lower()

    def test_initialize_campaign_with_character_name(self):
        """Test initializing campaign with character name."""
        result = CampaignLoader.initialize_campaign(
            "stormwreck-isle",
            character_name="Aragorn"
        )
        
        assert result["campaign_id"] == "stormwreck-isle"
        assert result["metadata"]["character_name"] == "Aragorn"
        # Character name alone doesn't modify the prompt, only with class
        assert result["initial_prompt"] is not None

    def test_initialize_campaign_with_both_character_fields(self):
        """Test initializing campaign with both class and name."""
        result = CampaignLoader.initialize_campaign(
            "stormwreck-isle",
            character_class="Wizard",
            character_name="Gandalf"
        )
        
        assert result["metadata"]["character_class"] == "Wizard"
        assert result["metadata"]["character_name"] == "Gandalf"
        assert "Gandalf" in result["initial_prompt"]
        # Check for wizard-related text (could be "Wizard" or "arcane" or "scholar")
        assert ("Wizard" in result["initial_prompt"] or 
                "arcane" in result["initial_prompt"].lower() or
                "scholar" in result["initial_prompt"].lower())

    def test_initialize_campaign_nonexistent(self):
        """Test initializing non-existent campaign raises error."""
        with pytest.raises(ValueError, match="Campaign.*not found"):
            CampaignLoader.initialize_campaign("nonexistent-campaign")

    def test_get_character_intro_fighter(self):
        """Test character intro generation for Fighter."""
        intro = CampaignLoader._get_character_intro("Fighter", "Aragorn")
        assert "Aragorn" in intro
        assert "Fighter" in intro or "warrior" in intro.lower() or "battle" in intro.lower()

    def test_get_character_intro_wizard(self):
        """Test character intro generation for Wizard."""
        intro = CampaignLoader._get_character_intro("Wizard", "Gandalf")
        assert "Gandalf" in intro
        assert "Wizard" in intro or "arcane" in intro.lower() or "spell" in intro.lower()

    def test_get_character_intro_unknown_class(self):
        """Test character intro for unknown class uses default."""
        intro = CampaignLoader._get_character_intro("UnknownClass", "TestName")
        assert "TestName" in intro
        assert "adventurer" in intro.lower()

    def test_initialize_campaign_metadata(self):
        """Test campaign initialization includes proper metadata."""
        result = CampaignLoader.initialize_campaign(
            "stormwreck-isle",
            character_class="Rogue",
            character_name="Shadow"
        )
        
        metadata = result["metadata"]
        assert "difficulty" in metadata
        assert metadata["character_class"] == "Rogue"
        assert metadata["character_name"] == "Shadow"

