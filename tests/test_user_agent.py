from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from urlcheck_smith.core.user_agent import get_default_user_agent


@patch("urlcheck_smith.core.user_agent.metadata.version")
def test_get_default_user_agent_uses_package_version(mock_version):
    mock_version.return_value = "0.3.1"

    assert get_default_user_agent() == "UrlCheckSmith/0.3.1"
    mock_version.assert_called_once_with("urlcheck-smith")


@patch("urlcheck_smith.core.user_agent.metadata.version")
def test_get_default_user_agent_falls_back_to_dev(mock_version):
    mock_version.side_effect = PackageNotFoundError

    assert get_default_user_agent() == "UrlCheckSmith/dev"