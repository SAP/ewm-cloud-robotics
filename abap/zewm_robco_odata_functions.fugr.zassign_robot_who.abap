**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zassign_robot_who.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"     REFERENCE(IV_WHO) TYPE  /SCWM/DE_WHO
*"  EXPORTING
*"     REFERENCE(ES_WHO) TYPE  /SCWM/WHO
*"  EXCEPTIONS
*"      ROBOT_NOT_FOUND
*"      WHO_NOT_FOUND
*"      WHO_LOCKED
*"      WHO_ASSIGNED
*"      WHT_ASSIGNED
*"      INTERNAL_ERROR
*"----------------------------------------------------------------------

  data: lv_robot_type type zewm_de_robot_type,
        lv_who        type /scwm/de_who,
        ls_rsrc       type /scwm/rsrc,
        lt_who        type /scwm/tt_who,
        lt_whoid      type /scwm/tt_whoid.

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

* Enqueue resource assignment to warehouse order
  call function 'ENQUEUE_EZEWM_ASSIGNROBO'
    exporting
      mode_/scwm/rsrc = 'X'
      mandt           = sy-mandt
      lgnum           = iv_lgnum
      rsrc            = iv_rsrc
      _scope          = '3'
      _wait           = abap_true
    exceptions
      foreign_lock    = 1
      system_failure  = 2
      others          = 3.
  if sy-subrc <> 0.
    raise internal_error.
  endif.

* Check if WHO is existing
  select single who from /scwm/wo_rsrc_ty into @lv_who  ##WARN_OK
        where
          lgnum = @iv_lgnum and
          who = @iv_who.

  if sy-subrc <> 0.
    raise who_not_found.
  endif.

  append iv_who to lt_whoid.

* Assign Warehouse Order to Resource
  call function 'ZASSIGN_WHO_TO_RSRC'
    exporting
      iv_lgnum           = iv_lgnum
      iv_rsrc            = iv_rsrc
      it_whoid           = lt_whoid
    importing
      et_who             = lt_who
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
* Prepare output
      read table lt_who into es_who index 1.
      if sy-subrc <> 0.
        clear es_who.
      endif.
    when 1.
      raise who_locked.
    when 2.
      raise wht_assigned.
    when 3.
      raise wht_assigned.
    when 4.
      raise internal_error.
    when 5.
      raise robot_not_found.
    when others.
      raise internal_error.
  endcase.

endfunction.
