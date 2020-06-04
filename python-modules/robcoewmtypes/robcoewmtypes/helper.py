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

"""Helper functions for robcoewmtypes."""

import os
import sys
import json

from datetime import datetime, timezone
from binascii import hexlify, unhexlify

from typing import Any, List, Union, Dict, Type

import attr


def create_robcoewmtype_str(obj: Any) -> str:
    """
    Create a type string from an robcoewm type class.

    This function should be used to save the data types of classes with "attr"
    attributes as a string to unstructure and restructure these classes later
    using "cattr" module.

    Input could be a class with "attr" attributes or a list of those classes.
    """
    # List of objects
    if isinstance(obj, list):
        clslist: List[Type[object]] = []
        clsmodulelist = []
        for entry in obj:
            # If data type is not collected yet, append it to list
            if entry.__class__ not in clslist:
                if not attr.has(entry.__class__):
                    raise TypeError(
                        '"{}" is not a class with "attr" attributes'.format(entry.__class__))
                clslist.append(entry.__class__)
                clsmodulelist.append(entry.__module__)

        # List with one data type
        if len(clslist) == 1:
            clsstr = 'List[{mod}.{cls}]'.format(mod=clsmodulelist[0], cls=clslist[0].__name__)
        # List with a union of data types
        else:
            clsstrlist = []
            # Convert class module and name to a string for all classes
            for clsmodule, cls in zip(clsmodulelist, clslist):
                clsstrlist.append('{mod}.{cls}'.format(mod=clsmodule, cls=cls.__name__))
            # Join class string list to a single string
            clsstr = 'List[Union[{clsjoin}]]'.format(clsjoin=','.join(clsstrlist))

    # Single object
    else:
        clsmodule = obj.__module__
        cls = obj.__class__
        # Check for class for attr attributes
        if not attr.has(cls):
            raise TypeError('"{}" is not a class with "attr" attributes'.format(cls))

        # Convert class module and name to a string
        clsstr = '{mod}.{cls}'.format(mod=clsmodule, cls=cls.__name__)

    return clsstr


def get_robcoewmtype(robcoewmtype_str: str) -> Any:
    """
    Return a robcoewm type class or a list of them.

    This function should be used to get data classes with "attr" attributes
    for their restructuring from JSON data using "cattr" module.

    Type string has to look like this.
    One object: robcoewmtypes.robot.Robot
    List of objects: List[robcoewmtypes.robot.Robot]
    List of different objects:
        List[Union[robcoewmtypes.robot.Robot
        robcoewmtypes.warehouseorder.WarehouseOrder]].
    """
    # First check if there is a List
    splittedlist = robcoewmtype_str.split('[')
    for i, line in enumerate(splittedlist):
        # first line
        if i == 0:
            # Either list or single class
            if line == 'List':
                islist = True
            else:
                islist = False
                classes_str = line.strip()
        # Second line
        elif i == 1:
            # Either Union or single class
            if line == 'Union':
                if not islist:
                    raise TypeError(
                        'Union only allowed in List. Actual structure: "{}"'.format(
                            robcoewmtype_str))
                isunion = True
            else:
                isunion = False
                # Remove ending ] and spaces
                classes_str = line.strip(']').strip()
        # Third line
        elif i == 2:
            if not islist or not isunion:
                raise TypeError(
                    'Supported nested structure: List[Union[<dataclasses>]]. '
                    'Actual structure: "{}"'.format(robcoewmtype_str))
            # Remove ending ] and spaces
            classes_str = line.strip(']').strip()
        # More than three lines
        else:
            raise TypeError(
                'Supported nested structure: List[Union[<dataclasses>]]. '
                'Actual structure: "{}"'.format(robcoewmtype_str))

    # Split dataclasses string to list of single data classes strings
    objlist = []
    for entry in classes_str.split(','):
        class_str = entry.split('.')
        # first line of the list has to include the module "robcoewmtypes"
        # second line is the package
        # third line is the type class
        for i, line in enumerate(class_str):
            # First line
            if i == 0:
                if line == 'robcoewmtypes':
                    module = sys.modules['robcoewmtypes']
                    obj = None
                else:
                    raise TypeError(
                        'Module must be "robcoewmtypes" not "{}"'.format(line))
            # Second line
            elif obj is None:
                obj = getattr(module, line)
            # All other lines
            else:
                obj = getattr(obj, line)

        # Check class for attr attributes
        if not attr.has(obj):  # type: ignore
            raise TypeError(
                '"{}" is not a class with "attr" attributes'.format(obj))
        else:
            objlist.append(obj)

    # At least one data class has to be found
    if not objlist:
        raise TypeError('No data classes found',
                        'Actual structure: "{}"'.format(robcoewmtype_str))

    if len(objlist) > 1 and not isunion:
        raise TypeError(
            'Only one object in structures without Union allowed',
            'Actual structure: "{}"'.format(robcoewmtype_str))

    # Return data types
    # Union for a single object vanishes, thus no need to differentiate those
    # cases here.
    if islist:
        return List[Union[tuple(objlist)]]  # type: ignore
    else:
        return Union[tuple(objlist)]


def strstrip(data: Any) -> str:
    """Convert input to string and strip it in one step."""
    return str(data).strip()


def validate_annotation(instance, attribute, value):
    """Validate if attribute type is the annotated one."""
    if not isinstance(value, attribute.type):
        raise TypeError(
            'Invalid type: Type of "{}" must be "{}"'.format(attribute.name, attribute.type))


def str_to_hex(string: str) -> str:
    """Convert a string to hex."""
    return hexlify(string.encode()).decode()


def hex_to_str(hexstr: str) -> str:
    """Convert a hex to string."""
    return unhexlify(hexstr).decode()


def get_sample_cr(crd: str) -> Dict:
    """Get a dictionary with a sample of a CR."""
    valid_crd = [
        'warehouseorder', 'robotrequest', 'robco_mission', 'robco_robot', 'robotconfiguration',
        'orderreservation', 'auctioneer', 'orderauction']
    if crd not in valid_crd:
        raise ValueError('There is no sample for CRD "{}"'.format(crd))
    path = os.path.dirname(__file__)
    with open('{}/k8s-files/sample_{}.json'.format(path, crd)) as file:
        template_cr = json.load(file)

    return template_cr


def datetime_now_iso() -> str:
    """Return datetime now() in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec='seconds')
