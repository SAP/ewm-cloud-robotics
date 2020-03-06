**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zconfirm_warehouse_task_step_1.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_TANUM) TYPE  /SCWM/TANUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"  EXPORTING
*"     REFERENCE(ET_LTAP_VB) TYPE  /SCWM/TT_LTAP_VB
*"  EXCEPTIONS
*"      WHT_NOT_CONFIRMED
*"      WHT_ALREADY_CONFIRMED
*"      INTERNAL_ERROR
*"----------------------------------------------------------------------

  data: lv_severity type bapi_mtype,
        ls_to_conf  type /scwm/to_conf,
        lt_bapiret  type bapirettab,
        lt_ltap_vb  type /scwm/tt_ltap_vb,
        lt_to_conf  type /scwm/to_conf_tt.

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

* Prepare input parameter for Warehouse Task confirmation
  ls_to_conf-tanum = iv_tanum.
  ls_to_conf-drsrc = iv_rsrc.
  append ls_to_conf to lt_to_conf.

  call function '/SCWM/TO_CONFIRM'
    exporting
      iv_lgnum         = iv_lgnum
      iv_wtcode        = wmegc_wtcode_rsrc
      iv_update_task   = abap_false
      iv_commit_work   = abap_false
      it_conf          = lt_to_conf
      iv_processor_det = abap_true
    importing
      et_bapiret       = lt_bapiret
      et_ltap_vb       = lt_ltap_vb
      ev_severity      = lv_severity.

* commit work and wait to ensure next OData calls is getting actual data
  commit work and wait.

* check errors
  if lv_severity ca 'EAX'.
    read table lt_bapiret with key type = 'E'
                                   id = '/SCWM/L3'
                                   number = 022
                                   transporting no fields.
    if sy-subrc = 0.
      raise wht_already_confirmed.
    else.
      raise wht_not_confirmed.
    endif.
  else.
    et_ltap_vb = lt_ltap_vb.
  endif.

endfunction.
