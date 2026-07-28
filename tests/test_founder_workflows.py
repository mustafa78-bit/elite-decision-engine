from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from decision.kernel.FounderOS import FounderOS, FounderBrief
from services.ollo.ollo_service import OLLOService
from services.ollo.parser import OLLOResponse


def test_founder_os_turkish_and_english_summaries():
    """Test that FounderOS correctly routes and answers Turkish and English summary requests."""
    fos = FounderOS()

    # 1. Turkish Summary Query
    resp_tr = fos.query("NEXUS, bugün piyasada bilmem gereken her şeyi özetle.")
    assert "Market Structure:" in resp_tr["answer"]
    assert "Portfolio Allocation:" in resp_tr["answer"]
    assert "özetle" in resp_tr["question"].lower()

    # 2. English Summary Query
    resp_en = fos.query("NEXUS, what should I know today?")
    assert "Market Structure:" in resp_en["answer"]
    assert "Portfolio Allocation:" in resp_en["answer"]
    assert "know" in resp_en["question"].lower()

    # 3. Turkish Greeting
    resp_greet_tr = fos.query("Günaydın, NEXUS.")
    assert "Market Structure:" in resp_greet_tr["answer"]

    # 4. English Greeting
    resp_greet_en = fos.query("Good morning, NEXUS.")
    assert "Market Structure:" in resp_greet_en["answer"]


def test_ollo_integration_with_founder_workflows():
    """Test that OLLOService correctly intercepts executive and natural language queries to FounderOS."""
    # Mock AI Service to avoid network I/O
    mock_ai = MagicMock()
    ollo = OLLOService(ai_service=mock_ai)

    # 1. Query Turkish summary
    resp_tr = ollo.query("NEXUS, bugün piyasada bilmem gereken her şeyi özetle.")
    assert isinstance(resp_tr, OLLOResponse)
    assert resp_tr.provider == "FounderOS"
    assert "Market Structure:" in resp_tr.text
    assert "Learning Summary:" in resp_tr.text

    # 2. Query English summary
    resp_en = ollo.query("What should I know today?")
    assert isinstance(resp_en, OLLOResponse)
    assert resp_en.provider == "FounderOS"
    assert "Market Structure:" in resp_en.text
