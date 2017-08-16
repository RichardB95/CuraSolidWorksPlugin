from . import utils


def getAvailableSolidWorksVersions():
    product_list = utils.getWindowsProducts(product_name = "SolidWorks")

    supported_versions = ["2016", "2017"]

    solidworks_product_list = []
    for product in product_list:
        for version in supported_versions:
            text = ("solidworks %s" % version).lower()
            if product["Name"].lower().startswith(text):
                solidworks_product_list.append(product)

    return solidworks_product_list
