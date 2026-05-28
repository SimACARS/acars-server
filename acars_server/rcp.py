"""
ACARS Server
Required Communication Performance Simulator
Ref: https://www.caa.co.uk/media/2cdpufa4/gold_2edition.pdf
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries

# Local Libraries


class RcpBase:
    """
    RCP Base Class
    """
    expiration_time: int # seconds
    target_time: int # seconds

    # RCP Time Allocations
    rcp_expiration_time: int # seconds
    rcp_target_time: int # seconds

    # TRN Time Allocations
    trn_expiration_time: int # seconds
    trn_target_time: int # seconds

    continuity_et: float # percentage
    continuity_tt: float # percentage
    availability: float # percentage
    integrity: int # max errors per hour


class Rcp180(RcpBase):
    """RCP Class"""
    expiration_time = 180
    target_time = 90
    rcp_expiration_time = 180
    rcp_target_time = 90
    trn_expiration_time = 180
    trn_target_time = 90
    continuity_et = 0.999
    continuity_tt = 0.95
    availability = 0.999
    integrity = 10


class Rcp240(RcpBase):
    """RCP Class"""
    expiration_time = 240
    target_time = 210
    rcp_expiration_time = 210
    rcp_target_time = 180
    trn_expiration_time = 150
    trn_target_time = 120
    continuity_et = 0.999
    continuity_tt = 0.95
    availability = 0.999
    integrity = 10


class Rcp400(RcpBase):
    """RCP Class"""
    expiration_time = 400
    target_time = 350
    rcp_expiration_time = 370
    rcp_target_time = 320
    trn_expiration_time = 310
    trn_target_time = 260
    continuity_et = 0.999
    continuity_tt = 0.95
    availability = 0.999
    integrity = 10


RCP_SLA = {
    "progress": "RCP240",
    "cpdlc": "RCP240",
    "telex": "RCP240",
    "ping": "RCP400",
    "posreq": "RCP240",
    "position": "RCP240",
    "datareq": "RCP240",
    "poll": "RCP240",
    "peek": "RCP240",
    "inforeq": "RCP400",
    "ads-c": "RCP180"
}
