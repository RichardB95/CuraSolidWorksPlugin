# Copyright (c) 2017 Ultimaker B.V.
# CuraSolidWorksPlugin is released under the terms of the LGPLv3 or higher.

import subprocess

##  If successful returns a list of all currently running processes, including
#   the following fields:
#   - Caption: Caption of the process, usually looks like this: "<something>.exe"
#   - ProcessId: process ID
#   If unsuccessful, return None.
def getAllRunningProcesses():
    columns = ["Caption", "ProcessId"]
    args = ["wmic", "/OUTPUT:STDOUT", "PROCESS", "get", ",".join(columns)]
    return _runWmicSearch(args, columns)


##  Searches for all Windows products using WMIC. The result is a list of
#   products including the following fields:
#   - InstallLocation
#   - Name
#   - Vendor
#   - Version
#
#   A "product_name" string can be provided so it will only look for products
#   whose name contains the <product_name> string.
#
def getWindowsProducts(product_name = None):
    columns = ["InstallLocation", "Name", "Vendor", "Version"]
    args = ["wmic", "/OUTPUT:STDOUT", "PRODUCT"]
    if product_name:
        args += ["where", "Name LIKE \'%%%s%%\'" % product_name]
    args += ["get", ",".join(columns)]

    return _runWmicSearch(args, columns)


def _runWmicSearch(args, columns):
    p = subprocess.Popen(args, stdout=subprocess.PIPE)

    out, _ = p.communicate()
    out = out.decode("utf-8")

    # sanitize the newline characters
    out = out.replace("\r\n", "\n")
    out = out.replace("\r", "\n")
    while out.find("\n\n") != -1:
        out = out.replace("\n\n", "\n")

    lines = out.split("\n")
    if len(lines) < 2:
        return

    # the first line is header
    headers = []
    header_line = lines[0].strip() + " "
    for i, column in enumerate(columns):
        start_idx = header_line.find(column + " ")
        end_idx = None
        if i + 1 < len(columns):
            end_idx = header_line.find(columns[i + 1] + " ")

        headers.append({"name": column,
                        "start_index": start_idx,
                        "end_index": end_idx})

    result_list = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        result = {}
        for header_info in headers:
            if header_info["end_index"] is not None:
                data = line[header_info["start_index"]:header_info["end_index"]]
            else:
                data = line[header_info["start_index"]:]

            result[header_info["name"]] = data.strip()

        result_list.append(result)
    return result_list
