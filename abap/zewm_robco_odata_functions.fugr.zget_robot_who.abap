**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zget_robot_who .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"     REFERENCE(IV_ENQUEUE) TYPE  ABAP_BOOL DEFAULT 'X'
*"  EXPORTING
*"     REFERENCE(ET_WHO) TYPE  /SCWM/TT_WHO
*"  EXCEPTIONS
*"      ROBOT_NOT_FOUND
*"      NO_ORDER_FOUND
*"      INTERNAL_ERROR
*"----------------------------------------------------------------------

  data: lv_robot_type type zewm_de_robot_type,
        ls_rsrc       type /scwm/rsrc,
        lt_wo_rsrc_ty type /scwm/tt_wo_rsrc_ty.


* Get robot master data
  call function '/SCWM/RSRC_READ_SINGLE'
    exporting
      iv_lgnum    = iv_lgnum
      iv_rsrc     = iv_rsrc
    importing
      es_rsrc     = ls_rsrc
    exceptions
      wrong_input = 1
      not_found   = 2
      others      = 3.

  if sy-subrc <> 0.
    raise robot_not_found.
  else.
* Check if resource is a robot
    select single robot_type from zewm_trsrc_typ into @lv_robot_type
      where lgnum = @iv_lgnum and
            rsrc_type = @ls_rsrc-rsrc_type.
    if sy-subrc <> 0.
      raise robot_not_found.
    endif.
  endif.

* Enqueue resource assignment to warehouse order if requested
  if iv_enqueue = abap_true.
    call function 'ENQUEUE_EZEWM_ASSIGNROBO'
      exporting
        mode_/scwm/rsrc = 'X'
        mandt           = sy-mandt
        lgnum           = iv_lgnum
        rsrc            = iv_rsrc
        _scope          = '2'
        _wait           = abap_true
      exceptions
        foreign_lock    = 1
        system_failure  = 2
        others          = 3.
    if sy-subrc <> 0.
      raise internal_error.
    endif.
  endif.  "if iv_enqueue = abap_true.

* Get WHO assigend to the robot
  call function 'ZGET_ASSIGNED_ROBOT_WHO'
    exporting
      iv_lgnum      = iv_lgnum
      iv_rsrc       = iv_rsrc
    importing
      et_wo_rsrc_ty = lt_wo_rsrc_ty.

  if lt_wo_rsrc_ty is initial.
    raise no_order_found.
  endif.

* Get complete data for warehouse orders
  select * from /scwm/who into table @et_who
    for all entries in @lt_wo_rsrc_ty
      where lgnum = @lt_wo_rsrc_ty-lgnum and
            who = @lt_wo_rsrc_ty-who.
  if sy-subrc <> 0.
    raise no_order_found.
  endif.

endfunction.
