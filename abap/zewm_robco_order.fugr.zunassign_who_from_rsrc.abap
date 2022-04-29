**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
**
function zunassign_who_from_rsrc .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IT_WHOID) TYPE  /SCWM/TT_WHOID
*"  EXCEPTIONS
*"      WHO_LOCKED
*"      WHO_IN_PROCESS
*"      WHO_NOT_UNASSIGNED
*"      WHO_NOT_FOUND
*"----------------------------------------------------------------------

  field-symbols: <who> type /scwm/s_who_int.

  data: lt_who     type /scwm/tt_who_int,
        ls_rsrc    type /scwm/s_rsrc,
        ls_ordim_o type /scwm/ordim_o,
        lt_ordim_o type /scwm/tt_ordim_o.

* Select WO to check if already locked
  try.
      call function '/SCWM/WHO_SELECT'
        exporting
          iv_to       = 'X'
          iv_lgnum    = iv_lgnum
          iv_lock_who = 'X'
          it_who      = it_whoid
        importing
          et_ordim_o  = lt_ordim_o.

    catch /scwm/cx_core.
      call function 'DEQUEUE_ALL'.

      raise who_locked.
  endtry.

* Check if WHO is existing
  select * from /scwm/who into table @lt_who
    for all entries in @it_whoid
        where
          lgnum = @iv_lgnum and
          who = @it_whoid-who.
  if sy-subrc <> 0.
    raise who_not_found.
  endif.

  sort lt_ordim_o by lgnum who tanum.

  loop at lt_ordim_o into ls_ordim_o.
    read table lt_who assigning <who> with key who = ls_ordim_o-who.
    if sy-subrc ne 0.
      exit.
    endif.
    if ls_ordim_o-srsrc is not initial and
       <who>-status = wmegc_wo_in_process.
      call function 'DEQUEUE_ALL'.

      raise who_in_process.
    endif.
  endloop.

  ls_rsrc-lgnum = iv_lgnum.

* Unassign warehouse order from a resource
  call function '/SCWM/RSRC_WHO_UNASSIGN'
    exporting
      it_who        = lt_who
      is_rsrc       = ls_rsrc
    exceptions
      error_message = 1
      others        = 2.
  if sy-subrc <> 0.
    raise who_not_unassigned.
  endif.

endfunction.
