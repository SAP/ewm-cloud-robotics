**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
**
function zset_robot_status.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"     REFERENCE(IV_EXCCODE) TYPE  /SCWM/DE_EXCCODE
*"  EXPORTING
*"     REFERENCE(ES_RSRC) TYPE  /SCWM/RSRC
*"  EXCEPTIONS
*"      ROBOT_NOT_FOUND
*"      STATUS_NOT_SET
*"----------------------------------------------------------------------

  data: lv_robot_type type zewm_de_robot_type,
        ls_rsrc       type /scwm/rsrc.

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

  try.
      call function 'ZEWM_ROBOT_RSRC_SET_STAT'
        exporting
          iv_lgnum   = iv_lgnum
          iv_rsrc    = iv_rsrc
          iv_exccode = iv_exccode
          iv_set_by  = 'B'.
    catch /scwm/cx_mfs.
      raise status_not_set.
  endtry.

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

  if sy-subrc = 0.
    es_rsrc = ls_rsrc.
  endif.

endfunction.
