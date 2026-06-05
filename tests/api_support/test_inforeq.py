"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
import requests

# Third Party Libraries
import pytest

# Local Libraries
from acars_server.api.message_types.inforeq import Noaa, Vatsim


class TestNoaa:
    """Some NOAA tests"""

    wrong_icao = "ZZZY"
    aerodrome = "EGKK"

    def test_response_metar(self):
        """Test that a metar is returned"""
        response = Noaa.metar(self.aerodrome)
        check = re.match(r"\d{4}\/\d{2}\/(\d{2}) (\d{2}):(\d{2})\s([A-Z]{4}) (\d{6})Z", response)
        if check is None:
            pytest.skip(f"{self.aerodrome} not in {response}")
        assert check
        assert check.group(4) == self.aerodrome
        assert check.group(5) == f"{check.group(1)}{check.group(2)}{check.group(3)}"

    def test_response_taf(self):
        """Test that a TAF is returned"""
        response = Noaa.taf(self.aerodrome)
        check = re.match(
            r"\d{4}\/\d{2}\/(\d{2}) (\d{2}):(\d{2})\sTAF .* ([A-Z]{4}) (\d{6})Z", response)
        if check is None:
            pytest.skip(f"{self.aerodrome} not in {response}")
        assert check
        assert check.group(4) == self.aerodrome

    def test_response_shorttaf(self):
        """Test that a TAF is returned"""
        response = Noaa.shorttaf(self.aerodrome)
        print(response)
        check = re.match(
            r"\d{4}\/\d{2}\/(\d{2}) (\d{2}):(\d{2})\sTAF TAF ([A-Z]{4}) (\d{6})Z", response)
        if check is None:
            pytest.skip(f"{self.aerodrome} not in {response}")
        assert check
        assert check.group(4) == self.aerodrome

    def test_response_timeout_metar(self, mocker):
        """Test that a string is returned"""
        mock_error = mocker.patch("acars_server.common.logger.error")

        mocker.patch(
            "acars_server.api.message_types.inforeq.requests.get",
            side_effect=requests.exceptions.ReadTimeout
        )

        response = Noaa.metar(self.aerodrome)

        assert response == f"NO METAR AVAILABLE FOR {self.aerodrome.upper()}"

        mock_error.assert_called_once_with(
            f"Timeout while fetching METAR for {self.aerodrome.upper()}"
        )

    def test_response_timeout_taf(self, mocker):
        """Test that a string is returned"""
        mock_error = mocker.patch("acars_server.common.logger.error")

        mocker.patch(
            "acars_server.api.message_types.inforeq.requests.get",
            side_effect=requests.exceptions.ReadTimeout
        )

        response = Noaa.taf(self.aerodrome)

        assert response == f"NO TAF AVAILABLE FOR {self.aerodrome.upper()}"

        mock_error.assert_called_once_with(
            f"Timeout while fetching TAF for {self.aerodrome.upper()}"
        )

    def test_response_timeout_shorttaf(self, mocker):
        """Test that a string is returned"""
        mock_error = mocker.patch("acars_server.common.logger.error")

        mocker.patch(
            "acars_server.api.message_types.inforeq.requests.get",
            side_effect=requests.exceptions.ReadTimeout
        )

        response = Noaa.shorttaf(self.aerodrome)

        assert response == f"NO SHORT TAF AVAILABLE FOR {self.aerodrome.upper()}"

        mock_error.assert_called_once_with(
            f"Timeout while fetching SHORT TAF for {self.aerodrome.upper()}"
        )


class TestVatsim:
    """Vatsim Tests"""
    vatsim = Vatsim()
    aerodrome = "EGKK"
    wrong_aerodrome = "ZZZY"

    def test_response_atis(self):
        """Test getting an ATIS"""
        response = self.vatsim.get_atis(self.aerodrome)

        assert "ATIS" in response
        if self.aerodrome not in response:
            pytest.skip(f"{self.aerodrome} not in {response}")

    def test_response_metar(self):
        """Test that a metar is returned"""
        response = self.vatsim.get_metar(self.aerodrome)
        check = re.match(r"([A-Z]{4}) (\d{6})Z", response)
        assert check
        assert check.group(1) == self.aerodrome

    def test_response_atis_wrong_icao(self):
        """Test getting an ATIS"""
        response = self.vatsim.get_atis(self.wrong_aerodrome)
        assert response == f"NO ATIS AVAILABLE FOR {self.wrong_aerodrome}"

    def test_response_metar_wrong_icao(self):
        """Test that a metar is returned"""
        response = self.vatsim.get_metar(self.wrong_aerodrome)
        assert response == f"NO METAR AVAILABLE FOR {self.wrong_aerodrome}"
