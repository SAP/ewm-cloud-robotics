**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zget_new_robotgroup_who .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC_TYPE) TYPE  /SCWM/DE_RSRC_TYPE
*"     REFERENCE(IV_RSRC_GROUP) TYPE  /SCWM/DE_RSRC_GRP
*"     REFERENCE(IV_NO_WHO) TYPE  INT2
*"  EXPORTING
*"     REFERENCE(ET_WHO) TYPE  /SCWM/TT_WHO
*"  EXCEPTIONS
*"      NO_ORDER_FOUND
*"      NO_ROBOT_RESOURCE_TYPE
*"      INTERNAL_ERROR
*"----------------------------------------------------------------------

  data: lv_robot_type type zewm_de_robot_type,
        lt_whoid      type /scwm/tt_whoid,
        ls_wo_rsrc_ty type /scwm/wo_rsrc_ty,
        lt_wo_rsrc_ty type /scwm/tt_wo_rsrc_ty.

  select single robot_type from zewm_trsrc_typ into lv_robot_type
    where lgnum = iv_lgnum and
          rsrc_type = iv_rsrc_type.

  if sy-subrc <> 0.
    raise no_robot_resource_type.
  endif.

* Get Warehouse Orders for Resource Type and Group which are not assigned to a resource and not in process yet
  call function 'ZGET_UNASSIGNED_WHO_FOR_RG'
    exporting
      iv_lgnum      = iv_lgnum
      iv_rsrc_type  = iv_rsrc_type
      iv_rsrc_group = iv_rsrc_group
    importing
      et_wo_rsrc_ty = lt_wo_rsrc_ty.

* Collect only the requested number of WHO
  loop at lt_wo_rsrc_ty into ls_wo_rsrc_ty.
* Exit the loop when number of requested orders is reached
    if sy-tabix > iv_no_who.
      exit.
    endif.

    append ls_wo_rsrc_ty-who to lt_whoid.
  endloop.

* Don't assign WHO to resource (empty resource), but set status in process
  call function 'ZASSIGN_WHO_TO_RSRC'
    exporting
      iv_lgnum           = iv_lgnum
      iv_rsrc            = space
      it_whoid           = lt_whoid
      iv_set_ip_only     = abap_true
    importing
      et_who             = et_who
    exceptions
      who_locked         = 1
      wht_assigned       = 2
      who_assigned       = 3
      no_operating_env   = 4
      rsrc_not_found     = 5
      who_status_not_set = 6
      others             = 7.
  case sy-subrc.
    when 0.

    when 1 or 2.
      raise no_order_found.
    when others.
      raise internal_error.
  endcase.

endfunction.
