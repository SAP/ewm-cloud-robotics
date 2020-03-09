**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zset_who_in_process .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IT_WHOID) TYPE  /SCWM/TT_WHOID
*"     REFERENCE(IV_UNSET_IN_PROCESS) TYPE  ABAP_BOOL DEFAULT
*"       ABAP_FALSE
*"  EXPORTING
*"     REFERENCE(ET_WHO) TYPE  /SCWM/TT_WHO
*"  EXCEPTIONS
*"      WHO_LOCKED
*"      WHO_STATUS_NOT_UPDATED
*"----------------------------------------------------------------------

  data: lv_should_status type char1,
        lv_new_status    type char1,
        lt_who_int       type /scwm/tt_who_int,
        lt_who_range     type range of /scwm/who-who,
        ls_who_range     like line of lt_who_range.

  field-symbols: <ls_who_int> type /scwm/s_who_int.

* Set current and new status according to iv_unset parameter
  if iv_unset_in_process = abap_true.
    lv_should_status = wmegc_wo_in_process.
    lv_new_status = wmegc_wo_open.
  else.
    lv_should_status = wmegc_wo_open.
    lv_new_status = wmegc_wo_in_process.
  endif.

* Select WO to check if already locked
  try.
      call function '/SCWM/WHO_SELECT'
        exporting
          iv_to       = abap_true
          iv_lgnum    = iv_lgnum
          iv_lock_who = abap_true
          it_who      = it_whoid
        importing
          et_who      = lt_who_int.

    catch /scwm/cx_core.
      call function 'DEQUEUE_ALL'.
      raise who_locked.
  endtry.

  loop at lt_who_int assigning <ls_who_int>.
* Skip warehouse order if it is not in the correct status
    if <ls_who_int>-status <> lv_should_status.
      delete lt_who_int.
* Skip unsetting if warehouse order is already assigned to a resource
    elseif iv_unset_in_process = abap_true and <ls_who_int>-rsrc <> space.
      delete lt_who_int.
    else.
* Set new status for export
      <ls_who_int>-status = lv_new_status.
* Append Warehouse orders to ranges for DB UPDATE
      ls_who_range-sign = 'I'.
      ls_who_range-option = 'EQ'.
      ls_who_range-low = <ls_who_int>-who.
      append ls_who_range to lt_who_range.
    endif.  "if iv_unset = abap_false and <ls_who_int>-status <> wmegc_wo_open.
  endloop.

  if lt_who_range is not initial.
* DB table /scwm/who
* Set new status for warehouse orders
    update /scwm/who set status = @lv_new_status
      where who in @lt_who_range
        and lgnum = @iv_lgnum.

    if sy-subrc <> 0.
      rollback work.
      raise who_status_not_updated.
    endif.

* DB table /scwm/wo_rsrc_ty
* Set new status for warehouse orders
    update /scwm/wo_rsrc_ty set status = @lv_new_status
      where who in @lt_who_range
        and lgnum = @iv_lgnum.

    if sy-subrc <> 0.
      rollback work.
      raise who_status_not_updated.
    endif.

  endif.  "if lt_who_range is not initial.

* Move to export table
  move-corresponding lt_who_int to et_who.

endfunction.
