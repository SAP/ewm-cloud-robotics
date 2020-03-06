**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zget_new_robot_who .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC) TYPE  /SCWM/DE_RSRC
*"  EXPORTING
*"     REFERENCE(ES_WHO) TYPE  /SCWM/WHO
*"  EXCEPTIONS
*"      ROBOT_NOT_FOUND
*"      NO_ORDER_FOUND
*"      ROBOT_HAS_ORDER
*"      INTERNAL_ERROR
*"----------------------------------------------------------------------

  data: lv_robot_type type zewm_de_robot_type,
        ls_rsrc       type /scwm/rsrc,
        lt_who        type /scwm/tt_who,
        lt_whoid      type /scwm/tt_whoid,
        ls_wo_rsrc_ty type /scwm/wo_rsrc_ty,
        lt_wo_rsrc_ty type /scwm/tt_wo_rsrc_ty.

  field-symbols: <ls_who> type /scwm/who.


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

* Enqueue resource assignment to warehouse order
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

* Check if there is already an order assigned to the robot
  call function 'ZGET_ROBOT_WHO'
    exporting
      iv_lgnum        = iv_lgnum
      iv_rsrc         = iv_rsrc
    importing
      et_who          = lt_who
    exceptions
      robot_not_found = 1
      no_order_found  = 2
      internal_error  = 3
      others          = 4.
  case sy-subrc.
    when 0.
      loop at lt_who assigning <ls_who>.
* if warehouse order was not started yet, send it again in case the warehouse order was
* assigned in a previous call, but the OData interface got a read timeout then.
        if <ls_who>-started_at is initial.
          es_who = <ls_who>.
* Warehouse order found, exit loop
          exit.
* Robot has already an order assigned -> quit
        else.
          raise robot_has_order.
        endif.
      endloop.  "loop at lt_who assigning <ls_who>.
    when 1.
      raise robot_not_found.
    when 2.
* No order assigned -> continue
    when others.
      raise internal_error.
  endcase.

* Try to assign a new warehouse order if no order was found yet
  if es_who is initial.
* Get one WHO for the robot
    call function 'ZGET_UNASSIGNED_WHO_FOR_RG'
      exporting
        iv_lgnum      = iv_lgnum
        iv_rsrc_type  = ls_rsrc-rsrc_type
        iv_rsrc_group = ls_rsrc-rsrc_grp
      importing
        et_wo_rsrc_ty = lt_wo_rsrc_ty.

* Loop over all warehouse orders until the first order was assigned
    loop at lt_wo_rsrc_ty into ls_wo_rsrc_ty.
      clear lt_whoid.
      append ls_wo_rsrc_ty-who to lt_whoid.

* Assign Warehouse Order to Ressource
      call function 'ZASSIGN_WHO_TO_RSRC'
        exporting
          iv_lgnum               = iv_lgnum
          iv_rsrc                = iv_rsrc
          it_whoid               = lt_whoid
        importing
          et_who                 = lt_who
        exceptions
          who_locked             = 1
          wht_assigned           = 2
          who_assigned           = 3
          no_operating_env       = 4
          rsrc_not_found         = 5
          who_status_not_updated = 6
          others                 = 7.

      case sy-subrc.
        when 0.
* Prepare output
          read table lt_who into es_who index 1.
          if sy-subrc = 0.
* Warehouse order found, exit loop
            exit.
          else.
            clear es_who.
          endif.
        when 4.
          raise internal_error.
        when 5.
          raise robot_not_found.
        when others.
* Warehouse Order could not be assigned. Try the next one
          continue.
      endcase.

    endloop.  "loop at lt_wo_rsrc_ty into ls_wo_rsrc_ty.

  endif.  "if es_who is initial.

  if es_who is initial.
    raise no_order_found.
  endif.


endfunction.
