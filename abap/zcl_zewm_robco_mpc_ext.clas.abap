class ZCL_ZEWM_ROBCO_MPC_EXT definition
  public
  inheriting from ZCL_ZEWM_ROBCO_MPC
  create public .

public section.

  methods DEFINE
    redefinition .
protected section.
private section.
ENDCLASS.



CLASS ZCL_ZEWM_ROBCO_MPC_EXT IMPLEMENTATION.


  method define.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lo_entity_type  type ref to /iwbep/if_mgw_odata_entity_typ,
          lo_complex_type type ref to /iwbep/if_mgw_odata_cmplx_type.

    super->define( ).

* Disable conversion for Lsd property to avoid error "The argument '00.00.0000 00:00:00' cannot be interpreted as a number"
* For EntitySet WarehouseOrder
    lo_entity_type = model->get_entity_type( iv_entity_name = 'WarehouseOrder' ).
    lo_entity_type->get_property( 'Lsd' )->disable_conversion( ).
* For ComplexType NewWarehouseOrder
    lo_complex_type = model->get_complex_type( iv_cplx_type_name = 'NewWarehouseOrder' ).
    lo_complex_type->get_property( 'Lsd' )->disable_conversion( ).

  endmethod.
ENDCLASS.
