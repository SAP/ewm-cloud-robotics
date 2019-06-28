**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zassign_who_to_rsrc .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"     REFERENCE(IT_WHOID) TYPE  /SCWM/TT_WHOID
*"     REFERENCE(IV_SET_IP_ONLY) TYPE  XFELD DEFAULT ABAP_FALSE
*"  EXPORTING
*"     REFERENCE(ET_WHO) TYPE  /SCWM/TT_WHO
*"  EXCEPTIONS
*"      WHO_LOCKED
*"      WHT_ASSIGNED
*"      WHO_ASSIGNED
*"      NO_OPERATING_ENV
*"      RSRC_NOT_FOUND
*"      WHO_STATUS_NOT_SET
*"----------------------------------------------------------------------

  data: lv_append     type xfeld,
        ls_ordim_o    type /scwm/ordim_o,
        lt_ordim_o    type /scwm/tt_ordim_o,
        ls_rsrc       type /scwm/rsrc,
        ls_t346       type /scwm/t346,
        lt_who        type /scwm/tt_who,
        lt_who_int    type /scwm/tt_who_int,
        ls_wo_rsrc_ty type /scwm/wo_rsrc_ty,
        lt_wo_rsrc_ty type /scwm/tt_wo_rsrc_ty,
        lt_who_range  type range of /scwm/who-who,
        ls_who_range  like line of lt_who_range.

  field-symbols: <ls_who_int> type /scwm/s_who_int.

* Only when resource should be assigned, not when setting who "in process" only
  if iv_set_ip_only = space.
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
      raise rsrc_not_found.
    endif.
  endif.  "if iv_rsrc is not initial.

* Select WO to check if already locked
  try.
      call function '/SCWM/WHO_SELECT'
        exporting
          iv_to       = abap_true
          iv_lgnum    = iv_lgnum
          iv_lock_who = abap_true
          it_who      = it_whoid
        importing
          et_who      = lt_who_int
          et_ordim_o  = lt_ordim_o.

    catch /scwm/cx_core.
      call function 'DEQUEUE_ALL'.
      raise who_locked.
  endtry.

* Check if Warehouse Orders are already assigned to a Resource
  loop at lt_who_int assigning <ls_who_int>.
    if <ls_who_int>-rsrc <> space.
      raise who_assigned.
    endif.
  endloop.

  sort lt_ordim_o by lgnum who tanum.

  loop at lt_ordim_o into ls_ordim_o.
    read table lt_who_int assigning <ls_who_int> with key who = ls_ordim_o-who.
    if sy-subrc ne 0.
      exit.
    endif.
    if ls_ordim_o-srsrc is not initial and
      ( <ls_who_int>-status = wmegc_wo_in_process or
        iv_rsrc <> ls_ordim_o-srsrc ).
      call function 'DEQUEUE_ALL'.
      raise wht_assigned.
    endif.
  endloop.  "loop at lt_ordim_o into ls_ordim_o.

  loop at lt_who_int assigning <ls_who_int>.

    clear: ls_wo_rsrc_ty, lt_wo_rsrc_ty.

    move-corresponding <ls_who_int> to ls_wo_rsrc_ty.
    append ls_wo_rsrc_ty to lt_wo_rsrc_ty.

*   Read queue to get operating environment
    call function '/SCWM/T346_READ_SINGLE'
      exporting
        iv_lgnum  = ls_wo_rsrc_ty-lgnum
        iv_queue  = ls_wo_rsrc_ty-queue
      importing
        es_t346   = ls_t346
      exceptions
        not_found = 1
        others    = 2.
    if sy-subrc <> 0.
      raise no_operating_env.
    endif.

* Only when resource should be assigned, not when setting who "in process" only
    if iv_set_ip_only = space.
*   Select/assign warehouse order for a resource
      call function '/SCWM/RSRC_WHO_SELECT'
        exporting
          iv_rfrsrc         = ls_t346-rfrsrc
          iv_norsrc_upd     = abap_true
          iv_man_wo_sel     = abap_true
          iv_no_rec_call    = abap_true "NO REC-Control by call from NON RF-Environment
        changing
          cs_rsrc           = ls_rsrc
          ct_wo_rsrc_ty     = lt_wo_rsrc_ty
        exceptions
          no_rstyp_attached = 1
          others            = 2.

      if sy-subrc = 0.
* Only append Warehouse Order to output, if successfully assigned
        lv_append = abap_true.
      else.
        clear lv_append.
      endif.

    else.
* Always append Warehouse Order to output when setting orders only to status in process
      lv_append = abap_true.
    endif.

    if lv_append = abap_true.
* Append Warehouse orders to ranges for later DB UPDATE
      loop at lt_wo_rsrc_ty into ls_wo_rsrc_ty.
        ls_who_range-sign = 'I'.
        ls_who_range-option = 'EQ'.
        ls_who_range-low = ls_wo_rsrc_ty-who.
        append ls_who_range to lt_who_range.
      endloop.

* Append to output
      move-corresponding lt_wo_rsrc_ty to lt_who.
      append lines of lt_who to et_who.
    endif.

  endloop.  "loop at lt_who_int assigning <ls_who_int>.

  if lt_who_range is not initial.
* Set in process status for warehouse orders
    update /scwm/who set status = @wmegc_wo_in_process
      where who in @lt_who_range.

    if sy-subrc <> 0.
      rollback work.
      clear et_who.
      raise who_status_not_set.
    endif.
  endif.  "if lt_who_range is not initial.

endfunction.
