# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.model import Study
from gws.controller import Controller
from gws.queue import Queue, Job

from gena.protocol import Recon

class API:
    
    async def test_recon( data: dict = None ) -> dict:
        """
        Reconstruction 

        :param request: The request
        :type request: `fastapi.Request`
        :return: The json response
        :rtype: `dict`
        """
        
        #check_is_admin()
        
        recon = Recon()
        
        user = Controller.get_current_user()
        study = Study.get_default_instance()
        e = recon.create_experiment(user=user, study=study)
        
        job = Job(user=user, experiment=e)
        Queue.add(job, auto_start=True)            
        return e.to_json()