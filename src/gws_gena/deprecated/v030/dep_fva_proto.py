# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BadRequestException, Protocol, protocol_decorator


@protocol_decorator("FVAProto", human_name="Deprecated FVA protocol",
                    short_description="Flux variability analysis protocol", hide=True, deprecated_since='0.3.1',
                    deprecated_message="Use new version of FVA")
class FVAProto(Protocol):

    def configure_protocol(self) -> None:
        raise BadRequestException("This protocol is no longer maintained.")
