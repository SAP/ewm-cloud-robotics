#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
#
# This file is part of ewm-cloud-robotics
# (see https://github.com/SAP/ewm-cloud-robotics).
#
# This file is licensed under the Apache Software License, v. 2 except as noted
# otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
#

"""
Conversion functions for robcoewminterface.

Conversion only works with data classes created with python "attr" library.
In those data classes types of attr.ib must be annotated.
Examples of data classes could be found in module robcoewmtypes.warehouseorder.
"""

import logging
from typing import Any
import attr

from robcoewmtypes import ODATA_TYPE_MAP

_LOGGER = logging.getLogger(__name__)


def odata_to_attr(odata: dict) -> Any:
    """Convert OData json response to RobCo types."""
    # Check if data segment is existing
    if 'd' not in odata:
        _LOGGER.error('No valid OData content: %s', odata)
        return

    if 'results' in odata['d']:
        # List of OData sets
        return_list = []
        for entry in odata['d']['results']:
            # Collect results for each entry
            return_list.append(split_odata_set(entry))
        return return_list
    else:
        # Single OData set
        return_obj = split_odata_set(odata['d'])
        return return_obj


def split_odata_set(odata: dict) -> Any:
    """Split OData data set to list or single entry."""
    if 'results' in odata:
        # List of entries
        return_list = []
        for entry in odata['results']:
            # Call this method recursively
            return_list.append(map_single_odata_entry(entry))
        return return_list
    else:
        # Single entry
        return_obj = map_single_odata_entry(odata)
        return return_obj


def map_single_odata_entry(odata: dict) -> Any:
    """Map single OData set to RobCo type and return it."""
    # Complex data types have their method name on the first level.
    # This level has to be removed. Test for __metadata too, if there is an
    # OData type without any fields
    if len(odata) == 1 and '__metadata' not in odata:
        odata = list(odata.values())[0]

    # Get data type of OData entry
    try:
        odatatype = odata['__metadata']['type']
    except KeyError:
        _LOGGER.error(
            'No data type information in OData entry found: %s', odata)
        raise

    # Map OData type to RobCo type
    try:
        attrtype = ODATA_TYPE_MAP[odatatype]
    except KeyError:
        _LOGGER.error(
            'No RobCo data type for OData type "%s" found', odatatype)
        raise

    # Get RobCo type attributes as dict
    attributes = attr.fields_dict(attrtype)

    # Processing of OData entry. Mapping dict keys to RobCo attributes
    newattrs_dict = {}
    for okey, oval in odata.items():
        nested = False
        # Convention: RobCo attributes have the same name then OData
        # attributes but lower case
        if okey.lower() in attributes:
            # Nested objects
            if isinstance(oval, dict):
                if not issubclass(
                        attributes[okey.lower()].type.__origin__, list):  # type: ignore
                    raise AttributeError(
                        'Data modelling issue. "{}" should have a "List" '
                        'annotation'.format(okey.lower()))
                nested = True
            else:
                newattrs_dict[okey.lower()] = oval
        # In case of nested objects attribute name might be different
        # evaluation by data type
        elif isinstance(oval, dict):
            nested = True

        # Determination of nested attribute
        if nested:
            # Only elements with "__metadata" or "results" in their key
            # contain data
            if '__metadata' not in oval and 'results' not in oval:
                continue
            # Get nested object
            nested_obj = split_odata_set(oval)
            # Don't try adding empty objects
            if not nested_obj:
                continue
            # Loop over RobCo attributes to find the right attribute to
            # attach the nested object
            for akey, aval in attributes.items():
                # Nested objects are always stored in list attributes
                # Try because there is no __origin__ on types like str
                try:
                    if issubclass(aval.type.__origin__, list):  # type: ignore
                        # Type of elements in "List" annotations could be
                        # found __args__[0]
                        if (isinstance(nested_obj, aval.type.__args__[0])  # type: ignore
                                and not isinstance(nested_obj, list)):
                            newattrs_dict[akey] = [nested_obj]
                        elif isinstance(nested_obj[0], aval.type.__args__[0]):  # type: ignore
                            newattrs_dict[akey] = nested_obj
                except AttributeError:
                    continue

    # Create new instance of identified object and return it
    return_obj = attrtype(**newattrs_dict)
    return return_obj
