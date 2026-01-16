

from gws_core import BadRequestException, ConfigParams, View, ViewType


class NetworkView(View):

    _type: ViewType = ViewType.NETWORK
    _data: "Network"

    def __init__(self, data):
        super().__init__()
        self._check_and_set_data(data)

    def _check_and_set_data(self, data: dict):
        """
        Check the data and return.

        Must be overloaded to implement adhoc data checker
        """
        from ..network import Network
        if not isinstance(data, Network):
            raise BadRequestException(
                "NetworkView data must be an instance of Network")

        self._data = data

    # def to_dict(self, params: ConfigParams) -> dict:
        # if params["layout"] == "spring":
        #     dump_data = self._spring_layout(params)
        # else:
     #   dump_data = self._data.dumps(refresh_layout=True)
       # return {
        #    **super().to_dict(params),
        #   "data": dump_data
        # }

    def data_to_dict(self, params: ConfigParams) -> dict:
        return self._data.dumps(refresh_layout=True)

    # def _spring_layout(self, params: ConfigParams):
    #     full = params["full"]
    #     net = self._data
    #     graph = BipartiteGraph(net)

    #     dump_data = self._data.dumps(refresh_layout=True)

    #     pos = {}
    #     for comp_data in dump_data["metabolites"]:
    #         chebi_id = comp_data["chebi_id"]
    #         if chebi_id:
    #             layout = comp_data["layout"]
    #             if layout.get("x") is not None:
    #                 pos[chebi_id] = (layout.get("x"), layout.get("y"))

    #     if full:
    #         fixed = None
    #     else:
    #         fixed = [chebi_id for chebi_id, data in pos.items() if data[0] is not None]

    #     pos = nx.spring_layout(
    #         graph.get_nx_graph(), k=None, pos=pos, fixed=fixed,
    #         iterations=50, threshold=0.0001, weight=None, scale=1000, center=None, dim=2, seed=None
    #     )

    #     for comp_data in dump_data["metabolites"]:
    #         chebi_id = comp_data["chebi_id"]
    #         if chebi_id in pos:
    #             layout = comp_data["layout"]
    #             layout["x"] = pos[chebi_id][0]
    #             layout["y"] = pos[chebi_id][1]
    #             for cluster in layout["clusters"].values():
    #                 cluster["x"] = pos[chebi_id][0]
    #                 cluster["y"] = pos[chebi_id][1]

    #     return dump_data
