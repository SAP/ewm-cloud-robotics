function zget_in_process_who.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_RSRC_TYPE) TYPE  /SCWM/DE_RSRC_TYPE
*"     REFERENCE(IV_RSRC_GROUP) TYPE  /SCWM/DE_RSRC_GRP
*"  EXPORTING
*"     REFERENCE(ET_WHO) TYPE  /SCWM/TT_WHO
*"  EXCEPTIONS
*"      NO_ORDER_FOUND
*"      NO_ROBOT_RESOURCE_TYPE
*"----------------------------------------------------------------------

  data: lv_robot_type type zewm_de_robot_type,
        lt_wo_rsrc_ty type /scwm/tt_wo_rsrc_ty.

  select single robot_type from zewm_trsrc_typ into lv_robot_type
    where lgnum = iv_lgnum and
          rsrc_type = iv_rsrc_type.

  if sy-subrc <> 0.
    raise no_robot_resource_type.
  endif.

* Get unassigned orders for a resource type and group which are in process
  call function 'ZGET_UNASSIGNED_WHO_FOR_RG'
    exporting
      iv_lgnum                 = iv_lgnum
      iv_rsrc_type             = iv_rsrc_type
      iv_rsrc_group            = iv_rsrc_group
      iv_get_in_process_orders = abap_true
    importing
      et_wo_rsrc_ty            = lt_wo_rsrc_ty.

  if lt_wo_rsrc_ty is initial.
    raise no_order_found.
  endif.

  move-corresponding lt_wo_rsrc_ty to et_who.

endfunction.
