**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
**
function zewm_robot_rsrc_set_stat.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     VALUE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"     VALUE(IV_EXCCODE) TYPE  /SCWM/DE_EXCCODE
*"     VALUE(IV_SET_BY) TYPE  /SCWM/DE_MFS_SET_BY
*"     VALUE(IV_CHANGED_BY) TYPE  /SCWM/DE_CHANGED_BY OPTIONAL
*"     REFERENCE(IS_TELETOTAL) TYPE  /SCWM/S_MFS_TELETOTAL OPTIONAL
*"  RAISING
*"      /SCWM/CX_MFS
*"--------------------------------------------------------------------

* This FM sets the Exception code and therefore the status of a
* resource which is related to MFS.
* A commit work must be set outside this FM

  data: lv_exccode     type /scwm/de_exccode,
        lv_iprcode     type /scwm/de_iprcode,
        lv_errquan     type /scwm/de_err_quantifier,
        lv_exccode_old type /scwm/de_exccode,
        lv_iprcode_old type /scwm/de_iprcode,
        lv_errquan_old type /scwm/de_err_quantifier,
        lv_exec_step   type /scwm/de_exec_step,
        lv_tstmp       type tzntstmps,
        lv_robot_type  type zewm_de_robot_type,
        ls_rsrc        type /scwm/rsrc,
        ls_content     type /scwm/s_mfs_content,
        ls_texcoie     type /scwm/texcoie.

* check import parameter consistence
  if iv_set_by = wmegc_mfs_set_by_sgr.
    raise exception type /scwm/cx_mfs
      exporting
        textid   = /scwm/cx_mfs=>wrong_parameter
        mv_msgty = 'E'.
  endif.

* Authority check
  if iv_set_by = wmegc_mfs_set_by_usr.
    authority-check object '/SCWM/MFS'
             id '/SCWM/LGNU' field iv_lgnum
             id '/SCWM/PLC'  field space
             id 'ACTVT'      field '02'.

    if sy-subrc <> 0.
      gv_msgv1 = iv_lgnum.
      raise exception type /scwm/cx_mfs
        exporting
          textid   = /scwm/cx_mfs=>no_authority
          mv_msgty = 'E'
          mv_msgv1 = gv_msgv1.
    endif.
  endif.

  get time stamp field lv_tstmp.

* read resource
  select single for update * from /scwm/rsrc
    into ls_rsrc
    where lgnum = iv_lgnum
      and rsrc  = iv_rsrc.

  if sy-subrc is not initial.
    raise exception type /scwm/cx_mfs
      exporting
        textid   = /scwm/cx_mfs=>wrong_parameter
        mv_msgty = 'E'.
  endif.

  select single robot_type from zewm_trsrc_typ into lv_robot_type
    where lgnum = ls_rsrc-lgnum
      and rsrc_type = ls_rsrc-rsrc_type.

  if sy-subrc is not initial.
    raise exception type /scwm/cx_mfs
      exporting
        textid   = /scwm/cx_mfs=>wrong_parameter
        mv_msgty = 'E'.
  endif.

* set execution step depending on setting object
  if iv_set_by = wmegc_mfs_set_by_plc.
*   exception code set by plc
    lv_exec_step = wmegc_execstep_a0.
  else.
*   exception code set by user
    lv_exec_step = wmegc_execstep_a1.
*   Clear exception triggers background handling
    if iv_exccode is initial.
      lv_exec_step = wmegc_execstep_a0.
    endif.
  endif.

* check if exception code is set or delete.
  if iv_exccode is not initial.
    lv_exccode = iv_exccode.
  else.
    call function '/SCWM/TEXCOIE_READ_SINGLE'
      exporting
        iv_lgnum       = iv_lgnum
        iv_exccode_int = wmegc_exccodei_mfs4
      importing
        es_texcoie     = ls_texcoie
      exceptions
        others         = 99.

    if sy-subrc is initial.
*     exception code only for posting
      lv_exccode = ls_texcoie-exccode.
    endif.
  endif.

* Read and Post new exception code
  if lv_exccode is not initial.
*   set content
    ls_content-tele        = is_teletotal.
    ls_content-lgnum       = iv_lgnum.
    ls_content-rsrc        = iv_rsrc.
    ls_content-exccode     = iv_exccode.

*   call exception handling
    call function '/SCWM/MFS_EXCCODE_SET'
      exporting
        iv_lgnum      = iv_lgnum
        iv_exccode    = lv_exccode
        iv_buscon     = wmegc_buscon_mf4
        iv_exec_step  = lv_exec_step
        iv_changed_by = iv_changed_by
        is_content    = ls_content
      importing
        ev_errquan    = lv_errquan
        ev_iprcode    = lv_iprcode.

    if iv_exccode is initial.
*     if exccode is removed, errquan and iprcode must be initial
      clear: lv_errquan, lv_iprcode.
    endif.
  endif.

* read old exception code
  case  iv_set_by.
    when wmegc_mfs_set_by_plc.
      if ls_rsrc-exccode_user is not initial.
        call function '/SCWM/MFS_EXCCODE_READ'
          exporting
            iv_lgnum     = iv_lgnum
            iv_exccode   = ls_rsrc-exccode_user
            iv_buscon    = wmegc_buscon_mf4
            iv_exec_step = wmegc_execstep_a1
          importing
            ev_iprcode   = lv_iprcode_old
            ev_errquan   = lv_errquan_old.

        lv_exccode_old = ls_rsrc-exccode_user.
      endif.

    when wmegc_mfs_set_by_usr.
      if ls_rsrc-exccode_plc is not initial.
        call function '/SCWM/MFS_EXCCODE_READ'
          exporting
            iv_lgnum     = iv_lgnum
            iv_exccode   = ls_rsrc-exccode_plc
            iv_buscon    = wmegc_buscon_mf4
            iv_exec_step = wmegc_execstep_a0
          importing
            ev_iprcode   = lv_iprcode_old
            ev_errquan   = lv_errquan_old.

        lv_exccode_old = ls_rsrc-exccode_plc.
      endif.
  endcase.

* update overall exception code
  if lv_errquan >= lv_errquan_old and
     iv_exccode is not initial.
*   set new overall exception code
    ls_rsrc-exccode_overall = iv_exccode.
    ls_rsrc-iprcode_overall = lv_iprcode.
    ls_rsrc-errquan_overall = lv_errquan.
  else.
    ls_rsrc-exccode_overall = lv_exccode_old.
    ls_rsrc-iprcode_overall = lv_iprcode_old.
    ls_rsrc-errquan_overall = lv_errquan_old.
  endif.

  case  iv_set_by.
    when wmegc_mfs_set_by_plc.
*     update exception code PLC
      ls_rsrc-exccode_plc     = iv_exccode.
      ls_rsrc-exccode_plc_at  = lv_tstmp.
    when wmegc_mfs_set_by_usr.
*     update exception code User
      ls_rsrc-exccode_user    = iv_exccode.
      ls_rsrc-exccode_user_by = iv_changed_by.
      ls_rsrc-exccode_user_at = lv_tstmp.
  endcase.

* update Resource on DB
  update /scwm/rsrc from ls_rsrc.

endfunction.
