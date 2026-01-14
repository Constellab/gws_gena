from gws_core import TypingStyle, resource_decorator

from ..fba.fba_result import FBAResult


@resource_decorator(
    "FVAResult",
    human_name="FVA result",
    short_description="Flux variability analysis result",
    hide=True,
    style=TypingStyle.material_icon(material_icon_name="troubleshoot", background_color="#F9EF1F"),
)
class FVAResult(FBAResult):
    """
    FVAResult class

    A resource object containing the result of a flux variability analysis.
    """
