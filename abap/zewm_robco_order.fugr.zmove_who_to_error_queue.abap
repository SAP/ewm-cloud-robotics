**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
**
function zmove_who_to_error_queue .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IS_RSRC) TYPE  /SCWM/RSRC
*"     REFERENCE(IV_WHO) TYPE  /SCWM/DE_WHO
*"  EXPORTING
*"     REFERENCE(EV_QUEUE) TYPE  /SCWM/RSRC-QUEUE
*"  EXCEPTIONS
*"      ROBOT_NOT_FOUND
*"      WHO_NOT_FOUND
*"      WHO_LOCKED
*"      NO_ERROR_QUEUE
*"      QUEUE_NOT_CHANGED
*"----------------------------------------------------------------------

  data: ls_who        type /scwm/s_who_int,
        lt_wo_rsrc_ty type /scwm/tt_wo_rsrc_ty,
        ls_wo_rsrc_ty type /scwm/wo_rsrc_ty,
        ls_attributes type /scwm/s_who_att,
        ls_t346       type /scwm/t346,
        lv_queue      type /scwm/rsrc-queue,
        lc_x          type xfeld value 'X'.

* Check if warehouse order exists
  try.
      call function '/SCWM/WHO_SELECT'
        exporting
          iv_lgnum    = iv_lgnum
          iv_who      = iv_who
          iv_lock_who = abap_true
        importing
          es_who      = ls_who.
    catch /scwm/cx_core.
      call function 'DEQUEUE_ALL'.
      raise who_locked.
  endtry.

* Check if the warehouse order was found
  if ls_who is initial.
    raise who_not_found.
  endif.


* Get error queue
* First try to get error queue from resource group
  select single zewm_error_queue from /scwm/trsrc_grp into @lv_queue
    where lgnum = @iv_lgnum and
          rsrc_grp = @is_rsrc-rsrc_grp.
  if sy-subrc <> 0.
    clear lv_queue.
  endif.

* If error queue is still initial, get it from resource type
  if lv_queue is initial.
    select single error_queue from zewm_trsrc_typ into @lv_queue
      where lgnum = @iv_lgnum and
            rsrc_type = @is_rsrc-rsrc_type.
    if sy-subrc <> 0.
      raise robot_not_found.
    endif.
  endif.

  if lv_queue is initial.
    raise no_error_queue.
  endif.

*   Check queue
  call function '/SCWM/T346_READ_SINGLE'
    exporting
      iv_lgnum  = iv_lgnum
      iv_queue  = lv_queue
    importing
      es_t346   = ls_t346
    exceptions
      not_found = 1
      others    = 2.
  if sy-subrc <> 0.
    raise queue_not_changed.
  endif.

*   Aggregate warehouse orders
  ls_wo_rsrc_ty-who = ls_who-who.
  append ls_wo_rsrc_ty to lt_wo_rsrc_ty.

*   Get index records for all WOs
  call function '/SCWM/RSRC_WHO_RSTYP_GET'
    exporting
      iv_lgnum      = iv_lgnum
      iv_rfind      = lc_x
    changing
      ct_wo_rsrc_ty = lt_wo_rsrc_ty.

*   Check whether each WHO has index records
*   If not raise an exception
  read table lt_wo_rsrc_ty into ls_wo_rsrc_ty
    with key who = ls_who-who.

  if ( ( sy-subrc ne 0 ) and
       ( ls_t346-rfrsrc = wmegc_rfrsrc_rs or
           ls_t346-rfrsrc = wmegc_rfrsrc_rf or
           ls_t346-rfrsrc = wmegc_rfrsrc_mfs_with_rsrc ) ).

* No index records found. Queue cannot be changed
    raise queue_not_changed.
  endif.

* Prepare warehouse order update
  move-corresponding ls_who to ls_attributes.
  ls_attributes-queue  = lv_queue.
  ls_attributes-lsd    = ls_who-lsd.

  call function '/SCWM/WHO_UPDATE'
    exporting
      iv_lgnum      = iv_lgnum
      iv_db_update  = 'X'
      iv_who        = ls_who-who
      iv_queue      = 'X'
      is_attributes = ls_attributes
    exceptions
      read_error    = 1
      attributes    = 2
      others        = 3.

* If error occurs raise exception
  if sy-subrc <> 0.
    rollback work.
    raise queue_not_changed.
  else.
    commit work.
    ev_queue = lv_queue.
  endif.

endfunction.
