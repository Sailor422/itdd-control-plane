from pathlib import Path

import tests.integration.test_stage_e2_resolver as integration_module
import tools.itdd as tools_module


def test_local_test_and_tool_modules_resolve_from_checkout():
    checkout = Path(__file__).resolve().parents[1]
    assert Path(integration_module.__file__).resolve().is_relative_to(checkout)
    assert Path(tools_module.__file__).resolve().is_relative_to(checkout)
