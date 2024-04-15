
from typing import TypedDict

TwinDict = TypedDict("TwinDict", {
    "name": str,
    "networks": list,
    "contexts": list,
    "network_contexts": list
})
