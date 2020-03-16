**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zunset_who_in_process_status.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_WHO) TYPE  /SCWM/DE_WHO
*"  EXPORTING
*"     REFERENCE(ES_WHO) TYPE  /SCWM/WHO
*"  EXCEPTIONS
*"      WHO_NOT_FOUND
*"      WHO_LOCKED
*"      WHO_STATUS_NOT_UPDATED
*"      INTERNAL_ERROR
*"----------------------------------------------------------------------

  data: ls_who   type /scwm/who,
        lt_who   type /scwm/who,
        lt_whoid type /scwm/tt_whoid.

* Check if WHO is existing
  select single * from /scwm/who into @ls_who
        where
          lgnum = @iv_lgnum and
          who = @iv_who.

  if sy-subrc <> 0.
    raise who_not_found.
  endif.

  append ls_who-who to lt_whoid.

* Unset warehouse order in process status
  call function 'ZSET_WHO_IN_PROCESS'
    exporting
      iv_lgnum               = iv_lgnum
      it_whoid               = lt_whoid
      iv_unset_in_process    = abap_true
    exceptions
      who_locked             = 1
      who_status_not_updated = 2
      others                 = 3.

  case sy-subrc.
    when 0.
      clear ls_who-status.
      move-corresponding ls_who to es_who.
    when 1.
      raise who_locked.
    when 2.
      raise who_status_not_updated.
    when others.
      raise internal_error.
  endcase.

endfunction.
