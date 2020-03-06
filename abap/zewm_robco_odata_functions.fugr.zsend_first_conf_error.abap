**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zsend_first_conf_error .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"     REFERENCE(IV_WHO) TYPE  /SCWM/DE_WHO
*"     REFERENCE(IV_TANUM) TYPE  /SCWM/TANUM
*"  EXPORTING
*"     REFERENCE(ES_WHO) TYPE  /SCWM/WHO
*"  EXCEPTIONS
*"      ROBOT_NOT_FOUND
*"      WHO_NOT_FOUND
*"      WHO_LOCKED
*"      WHO_IN_PROCESS
*"      WHO_NOT_UNASSIGNED
*"      NO_ERROR_QUEUE
*"      QUEUE_NOT_CHANGED
*"      INTERNAL_ERROR
*"----------------------------------------------------------------------

  data: lv_robot_type type zewm_de_robot_type,
        ls_who        type /scwm/who,
        ls_rsrc       type /scwm/rsrc,
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

* Enqueue resource unassignment from warehouse order
  call function 'ENQUEUE_EZEWM_ASSIGNROBO'
    exporting
      mode_/scwm/rsrc = 'E'
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

* Check if warehouse order is existing
  select single * from /scwm/who into @ls_who
        where
          lgnum = @iv_lgnum and
          who = @iv_who.

  if sy-subrc <> 0.
    raise who_not_found.
  endif.

  append ls_who-who to lt_whoid.

* Move warehouse order to error queue
  call function 'ZMOVE_WHO_TO_ERROR_QUEUE'
    exporting
      iv_lgnum          = iv_lgnum
      is_rsrc           = ls_rsrc
      iv_who            = iv_who
    importing
      ev_queue          = ls_who-queue
    exceptions
      robot_not_found   = 1
      who_not_found     = 2
      who_locked        = 3
      no_error_queue    = 4
      queue_not_changed = 5
      others            = 6.

  case sy-subrc.
    when 0.
      es_who = ls_who.
    when 1.
      raise robot_not_found.
    when 2.
      raise who_not_found.
    when 3.
      raise who_locked.
    when 4.
      raise no_error_queue.
    when 5.
      raise queue_not_changed.
    when others.
      raise internal_error.
  endcase.

* Unassign warehouse order from resource
  call function 'ZUNASSIGN_WHO_FROM_RSRC'
    exporting
      iv_lgnum           = iv_lgnum
      it_whoid           = lt_whoid
    exceptions
      who_locked         = 1
      who_in_process     = 2
      who_not_unassigned = 3
      others             = 4.

  case sy-subrc.
    when 0.
      clear: ls_who-rsrc, es_who-rsrc.
    when 1.
      raise who_locked.
    when 2.
      raise who_in_process.
    when 3.
      raise who_not_unassigned.
    when others.
      raise internal_error.
  endcase.

* Write alert
  call function 'ZWHT_ROBOT_CONF_ERROR_ALERT'
    exporting
      iv_lgnum      = iv_lgnum
      iv_tanum      = iv_tanum
      iv_rsrc       = iv_rsrc
      iv_final_conf = abap_false.

* commit work and wait to ensure next OData calls is getting actual data
  commit work and wait.

endfunction.
