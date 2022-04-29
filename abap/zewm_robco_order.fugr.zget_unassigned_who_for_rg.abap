**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
**
function zget_unassigned_who_for_rg .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC_TYPE) TYPE  /SCWM/DE_RSRC_TYPE
*"     REFERENCE(IV_RSRC_GROUP) TYPE  /SCWM/DE_RSRC_GRP
*"     REFERENCE(IV_GET_IN_PROCESS_ORDERS) TYPE  ABAP_BOOL DEFAULT
*"       ABAP_FALSE
*"  EXPORTING
*"     REFERENCE(ET_WO_RSRC_TY) TYPE  /SCWM/TT_WO_RSRC_TY
*"----------------------------------------------------------------------

  data: lv_status     type char1,
        lt_trsgr_q_sq type table of /scwm/trsgr_q_sq,
        lt_wo_rsrc_ty type table of /scwm/wo_rsrc_ty.

  field-symbols: <ls_trsgr_q_sq> like line of lt_trsgr_q_sq.

* Either In Process or Open Warehouse Orders
  if iv_get_in_process_orders = abap_true.
    lv_status = wmegc_wo_in_process.
  else.
    lv_status = wmegc_wo_open.
  endif.

* Get queues for given resource group
  select queue from /scwm/trsgr_q_sq
    where lgnum = @iv_lgnum and
          rsrc_grp = @iv_rsrc_group
    order by seqno ascending
    into corresponding fields of table @lt_trsgr_q_sq.

  if sy-subrc <> 0.
    return.
  endif.

* Select WHO from all queues.
  loop at lt_trsgr_q_sq assigning <ls_trsgr_q_sq>.

    select * from /scwm/wo_rsrc_ty
      where
        lgnum = @iv_lgnum and
        rsrc_type = @iv_rsrc_type and
        queue = @<ls_trsgr_q_sq>-queue and
        status = @lv_status and
        rsrc = @space
      order by lsd ascending, priority descending, who ascending
      into table @lt_wo_rsrc_ty.

    if sy-subrc = 0.
      append lines of lt_wo_rsrc_ty to et_wo_rsrc_ty.
    endif.

  endloop.  "loop at lt_trsgr_q_sq assigning <ls_trsgr_q_sq>.

endfunction.
