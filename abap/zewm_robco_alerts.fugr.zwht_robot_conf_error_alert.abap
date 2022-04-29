**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
**
function zwht_robot_conf_error_alert .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_TANUM) TYPE  /SCWM/TANUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"     REFERENCE(IV_FINAL_CONF) TYPE  ABAP_BOOL
*"----------------------------------------------------------------------

  data: ls_alert_data    type /scmb/alert_data_str,
        lt_alert_data    type /scmb/alert_data_tab,
        ls_warehousetask type /scwm/ltap.
  constants: lc_alapplid type /sapapo/amoapplid value 'WME',
             lc_atid     type /scmb/atid        value '2506', "No Access to Storage Bin
             lc_alprio   type /scmb/alprio      value '1'.

*   set alert header data
  get time stamp field ls_alert_data-alvldfr.
  ls_alert_data-alvldto  = ls_alert_data-alvldfr.
  ls_alert_data-mandt    = sy-mandt.
  ls_alert_data-alapplid = lc_alapplid.
  ls_alert_data-atid     = lc_atid.
  ls_alert_data-alprio   = lc_alprio.

  ls_alert_data-almsgid  = '/SCWM/EXCEPTION'.
  ls_alert_data-almsgtyp = 'E'.
  ls_alert_data-almsgno  = '024'.
  if iv_final_conf = abap_false.
    ls_alert_data-almsgv1  = text-001.
  else.
    ls_alert_data-almsgv1  = text-002.
  endif.
  ls_alert_data-almsgv2 = text-003.
  replace '&1' with iv_rsrc into ls_alert_data-almsgv2.

* Get data of warehouse task
  select single * from /scwm/ordim_o into corresponding fields of @ls_warehousetask
    where lgnum = @iv_lgnum
      and tanum = @iv_tanum.
  if sy-subrc <> 0.
    ls_warehousetask-lgnum = iv_lgnum.
    ls_warehousetask-tanum = iv_tanum.
  endif.

*   map alert data
  call method /scwm/cl_exception=>map_data_alert
    exporting
      is_appl_item_data = ls_warehousetask
      is_alt_struc_name = '/SCWM/ALPRM2501'
    changing
      cs_alert_data     = ls_alert_data.

*   write alert
  append ls_alert_data to lt_alert_data.
  call method /scmb/alen=>alert_write
    exporting
      iv_update_task = abap_false
    changing
      ct_alert_data  = lt_alert_data.


endfunction.
