# Copyright (c) 2016 Thomas Karl Pietrowski

# TODO: Adding support for basic CATIA support

import os
import sys

external_modules = os.path.join(os.path.split(__file__)[0], "3rd_party")
if os.path.isdir(external_modules):
    sys.path.append(external_modules)

from UM.Platform import Platform

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("CuraSolidWorksIntegrationPlugin")

if Platform.isWindows():
    # For installation check
    import winreg
    # The reader plugin itself
    from . import SolidWorksReader

    def is_SolidWorks_available():
        try:
            # Could find a better key to detect whether CATIA is installed..
            winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "SldWorks.Application")
            return True
        except:
            return False

def getMetaData():
    return {"plugin": {
                "name": i18n_catalog.i18nc("@label", "SolidWorksIntegrationPlugin"),
                "author": "Thomas Karl Pietrowski",
                "version": "0.1.0",
                "description": i18n_catalog.i18nc("@info:whatsthis", "Gives you the possibility to open files via SolidWorks itself."),
                "api": 3
            },
            "mesh_reader": [
                {
                    "extension": "SLDPRT",
                    "description": i18n_catalog.i18nc("@item:inlistbox", "SolidWorks part file")
                },
                {
                    "extension": "SLDASM",
                    "description": i18n_catalog.i18nc("@item:inlistbox", "SolidWorks assembly file")
                },
                


                # Needs more documentation on how to convert a CATproduct in CATIA using COM API
                #
                #{
                #    "extension": "CATProduct",
                #    "description": i18n_catalog.i18nc("@item:inlistbox", "CATproduct file")
                #}
            ]
		}

def register(app):
    if Platform.isWindows():
        reader = SolidWorksReader.SolidWorksReader()
        if is_SolidWorks_available() and reader.areReadersAvailable():
            return {"mesh_reader": reader}
    return {}
