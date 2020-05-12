class ZCL_ZEWM_ROBCO_DPC_EXT definition
  public
  inheriting from ZCL_ZEWM_ROBCO_DPC
  create public .

public section.

  constants GC_ERROR_RNF type STRING value 'ROBOT_NOT_FOUND' ##NO_TEXT.
  constants GC_ERROR_NOF type STRING value 'NO_ORDER_FOUND' ##NO_TEXT.
  constants GC_ERROR_RSN type STRING value 'ROBOT_STATUS_NOT_SET' ##NO_TEXT.
  constants GC_ERROR_IE type STRING value 'INTERNAL_ERROR' ##NO_TEXT.
  constants GC_ERROR_NRT type STRING value 'NO_RESOURCE_TYPE' ##NO_TEXT.
  constants GC_ERROR_NRG type STRING value 'NO_RESOURCE_GROUP' ##NO_TEXT.
  constants GC_ERROR_RAE type STRING value 'RESOURCE_EXISTING' ##NO_TEXT.
  constants GC_ERROR_RNR type STRING value 'RESOURCE_TYPE_IS_NO_ROBOT' ##NO_TEXT.
  constants GC_ERROR_DUF type STRING value 'DB_UPDATE_FAILED' ##NO_TEXT.
  constants GC_ERROR_WOA type STRING value 'WAREHOUSE_ORDER_ASSIGNED' ##NO_TEXT.
  constants GC_ERROR_WTA type STRING value 'WAREHOUSE_TASK_ASSIGNED' ##NO_TEXT.
  constants GC_ERROR_WOL type STRING value 'WAREHOUSE_ORDER_LOCKED' ##NO_TEXT.
  constants GC_ERROR_RNE type STRING value 'RESOURCE_GROUP_NOT_EXISTING' ##NO_TEXT.
  constants GC_ERROR_ECP type STRING value 'ERROR_CREATING_PICKHU' ##NO_TEXT.
  constants GC_ERROR_QNE type STRING value 'QUEUE_NOT_EXISTING' ##NO_TEXT.
  constants GC_ERROR_UBI type STRING value 'URL_PARAM_BODY_INCONSISTENT' ##NO_TEXT.
  constants GC_ERROR_WNC type STRING value 'WAREHOUSE_TASK_NOT_CONFIRMED' ##NO_TEXT.
  constants GC_ERROR_RHO type STRING value 'ROBOT_HAS_ORDER' ##NO_TEXT.
  constants GC_ERROR_WIP type STRING value 'WAREHOUSE_ORDER_IN_PROCESS' ##NO_TEXT.
  constants GC_ERROR_WNU type STRING value 'WAREHOUSE_ORDER_NOT_UNASSIGNED' ##NO_TEXT.
  constants GC_ERROR_NEQ type STRING value 'NO_ERROR_QUEUE_FOUND' ##NO_TEXT.
  constants GC_ERROR_QNC type STRING value 'QUEUE_NOT_CHANGED' ##NO_TEXT.
  constants GC_ERROR_WAC type STRING value 'WAREHOUSE_TASK_ALREADY_CONFIRMED' ##NO_TEXT.
  constants GC_ERROR_WSN type STRING value 'WAREHOUSE_ORDER_STATUS_NOT_UPDATED' ##NO_TEXT.
  constants GC_ERROR_FLK type STRING value 'FOREIGN_LOCK' ##NO_TEXT.
  constants GC_ERROR_NOA type STRING value 'NO_AUTHORIZATION' ##NO_TEXT.

  methods /IWBEP/IF_MGW_APPL_SRV_RUNTIME~EXECUTE_ACTION
    redefinition .
protected section.

  methods OPENWAREHOUSETAS_GET_ENTITY
    redefinition .
  methods OPENWAREHOUSETAS_GET_ENTITYSET
    redefinition .
  methods RESOURCEGROUPDES_GET_ENTITY
    redefinition .
  methods RESOURCEGROUPDES_GET_ENTITYSET
    redefinition .
  methods RESOURCEGROUPSET_GET_ENTITY
    redefinition .
  methods RESOURCEGROUPSET_GET_ENTITYSET
    redefinition .
  methods RESOURCETYPEDESC_GET_ENTITY
    redefinition .
  methods RESOURCETYPEDESC_GET_ENTITYSET
    redefinition .
  methods ROBOTRESOURCETYP_GET_ENTITY
    redefinition .
  methods ROBOTSET_CREATE_ENTITY
    redefinition .
  methods ROBOTSET_GET_ENTITY
    redefinition .
  methods ROBOTSET_GET_ENTITYSET
    redefinition .
  methods ROBOTSET_UPDATE_ENTITY
    redefinition .
  methods STORAGEBINSET_GET_ENTITY
    redefinition .
  methods STORAGEBINSET_GET_ENTITYSET
    redefinition .
  methods WAREHOUSEDESCRIP_GET_ENTITY
    redefinition .
  methods WAREHOUSEDESCRIP_GET_ENTITYSET
    redefinition .
  methods WAREHOUSENUMBERS_GET_ENTITY
    redefinition .
  methods WAREHOUSENUMBERS_GET_ENTITYSET
    redefinition .
  methods WAREHOUSEORDERSE_GET_ENTITY
    redefinition .
  methods WAREHOUSEORDERSE_GET_ENTITYSET
    redefinition .
  methods ROBOTRESOURCETYP_GET_ENTITYSET
    redefinition .
private section.
ENDCLASS.



CLASS ZCL_ZEWM_ROBCO_DPC_EXT IMPLEMENTATION.


  method /iwbep/if_mgw_appl_srv_runtime~execute_action.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_conf_exc_str	     type char4,
          lv_exccode           type /scwm/de_exccode,
          lv_lgnum             type /scwm/lgnum,
          lv_no_who            type int2,
          lv_rsrc              type /scwm/de_rsrc,
          lv_rsrc_group        type /scwm/de_rsrc_grp,
          lv_rsrc_type         type /scwm/de_rsrc_type,
          lv_who               type /scwm/de_who,
          lv_tanum             type /scwm/tanum,
          lv_nista             type /scwm/ltap_nista,
          lv_altme             type /scwm/de_aunit,
          lv_nlpla             type /scwm/ltap_nlpla,
          lv_nlenr             type /scwm/de_deshu,
          lv_parti             type /scwm/ltap_conf_parti,
          ls_robot             type zcl_zewm_robco_mpc=>ts_robot,
          ls_rsrc              type /scwm/rsrc,
          ls_who               type /scwm/who,
          ls_warehouseorder    type zcl_zewm_robco_mpc=>ts_warehouseorder,
          ls_newwarehouseorder type zcl_zewm_robco_mpc=>newwarehouseorder,
          lt_ltap_vb           type /scwm/tt_ltap_vb,
          lt_warehouseorder    type zcl_zewm_robco_mpc=>tt_warehouseorder,
          lt_newwarehouseorder type table of zcl_zewm_robco_mpc=>newwarehouseorder,
          lt_warehousetaskconf type table of zcl_zewm_robco_mpc=>warehousetaskconfirmation,
          lt_who               type /scwm/tt_who.

    data(lv_action_name) = io_tech_request_context->get_function_import_name( ).
    data(lt_parameter) = io_tech_request_context->get_parameters( ).

    field-symbols: <ls_parameter>      like line of lt_parameter.

    case lv_action_name.
      when 'GetRobotWarehouseOrders' or 'GetInProcessWarehouseOrders'.
        authority-check object 'ZEWM_ROBCO'
          id 'ACTVT'  field '03'.

        if sy-subrc <> 0.
          raise exception type /iwbep/cx_mgw_busi_exception
            exporting
              textid           = /iwbep/cx_mgw_busi_exception=>business_error
              http_status_code = 401
              msg_code         = gc_error_noa
              message          = text-026.
        endif.
      when others.
        authority-check object 'ZEWM_ROBCO'
          id 'ACTVT'  field '02'.

        if sy-subrc <> 0.
          raise exception type /iwbep/cx_mgw_busi_exception
            exporting
              textid           = /iwbep/cx_mgw_busi_exception=>business_error
              http_status_code = 401
              msg_code         = gc_error_noa
              message          = text-026.
        endif.
    endcase.

    loop at lt_parameter assigning <ls_parameter>.
      case <ls_parameter>-name.
        when 'EXCCODE'.
          lv_exccode = <ls_parameter>-value.
        when 'LGNUM'.
          lv_lgnum = <ls_parameter>-value.
        when 'NO_WHO'.
          lv_no_who = <ls_parameter>-value.
        when 'RSRC'.
          lv_rsrc = <ls_parameter>-value.
        when 'RSRC_GRP'.
          lv_rsrc_group = <ls_parameter>-value.
        when 'RSRC_TYPE'.
          lv_rsrc_type = <ls_parameter>-value.
        when 'TANUM'.
          lv_tanum = <ls_parameter>-value.
        when 'NISTA'.
          lv_nista = <ls_parameter>-value.
        when 'ALTME'.
          lv_altme = <ls_parameter>-value.
        when 'NLPLA'.
          lv_nlpla = <ls_parameter>-value.
        when 'NLENR'.
          lv_nlenr = <ls_parameter>-value.
        when 'PARTI'.
          lv_parti  = <ls_parameter>-value.
        when 'WHO'.
          lv_who  = <ls_parameter>-value.
        when 'CONF_EXC'.
* Only one Exception code per message supported
          lv_conf_exc_str = <ls_parameter>-value.
      endcase.  "case <ls_parameter>-name.
    endloop.

    case lv_action_name.
      when 'GetRobotWarehouseOrders'.

        call function 'ZGET_ROBOT_WHO'
          exporting
            iv_lgnum        = lv_lgnum
            iv_rsrc         = lv_rsrc
          importing
            et_who          = lt_who
          exceptions
            robot_not_found = 1
            no_order_found  = 2
            internal_error  = 3
            others          = 4.

        case sy-subrc.
          when 0.
            move-corresponding lt_who to lt_warehouseorder.
            copy_data_to_ref( exporting is_data = lt_warehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnf
                message          = text-001.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'GetNewRobotWarehouseOrder'.

        call function 'ZGET_NEW_ROBOT_WHO'
          exporting
            iv_lgnum        = lv_lgnum
            iv_rsrc         = lv_rsrc
          importing
            es_who          = ls_who
          exceptions
            robot_not_found = 1
            no_order_found  = 2
            robot_has_order = 3
            internal_error  = 4
            others          = 5.

        case sy-subrc.
          when 0.
            move-corresponding ls_who to ls_newwarehouseorder.
            copy_data_to_ref( exporting is_data = ls_newwarehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnf
                message          = text-001.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 3.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rho
                message          = text-018.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'GetNewRobotTypeWarehouseOrders'.
        call function 'ZGET_NEW_ROBOTGROUP_WHO'
          exporting
            iv_lgnum               = lv_lgnum
            iv_rsrc_type           = lv_rsrc_type
            iv_rsrc_group          = lv_rsrc_group
            iv_no_who              = lv_no_who
          importing
            et_who                 = lt_who
          exceptions
            no_order_found         = 1
            no_robot_resource_type = 2
            others                 = 3.

        case sy-subrc.
          when 0.
            move-corresponding lt_who to lt_newwarehouseorder.
            copy_data_to_ref( exporting is_data = lt_newwarehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnr
                message          = text-008.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'GetInProcessWarehouseOrders'.
        call function 'ZGET_IN_PROCESS_WHO'
          exporting
            iv_lgnum               = lv_lgnum
            iv_rsrc_type           = lv_rsrc_type
            iv_rsrc_group          = lv_rsrc_group
          importing
            et_who                 = lt_who
          exceptions
            no_order_found         = 1
            no_robot_resource_type = 2
            others                 = 3.

        case sy-subrc.
          when 0.
            move-corresponding lt_who to lt_warehouseorder.
            copy_data_to_ref( exporting is_data = lt_warehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnr
                message          = text-008.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'SetRobotStatus'.
        call function 'ZSET_ROBOT_STATUS'
          exporting
            iv_lgnum       = lv_lgnum
            iv_rsrc        = lv_rsrc
            iv_exccode     = lv_exccode
          importing
            es_rsrc        = ls_rsrc
          exceptions
            status_not_set = 1
            others         = 2.

        case sy-subrc.
          when 0.
            move-corresponding ls_rsrc to ls_robot.
            copy_data_to_ref( exporting is_data = ls_robot
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rsn
                message          = text-004.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'AssignRobotToWarehouseOrder'.
        call function 'ZASSIGN_ROBOT_WHO'
          exporting
            iv_lgnum        = lv_lgnum
            iv_rsrc         = lv_rsrc
            iv_who          = lv_who
          importing
            es_who          = ls_who
          exceptions
            robot_not_found = 1
            who_not_found   = 2
            who_locked      = 3
            who_assigned    = 4
            wht_assigned    = 5
            internal_error  = 6
            others          = 7.
        case sy-subrc.
          when 0.
            move-corresponding ls_who to ls_warehouseorder.
            copy_data_to_ref( exporting is_data = ls_warehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnf
                message          = text-001.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 3.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wol
                message          = text-010.
          when 4.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_woa
                message          = text-011.
          when 5.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wta
                message          = text-012.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'ConfirmWarehouseTask'.

        call function 'ZCONFIRM_WAREHOUSE_TASK'
          exporting
            iv_lgnum              = lv_lgnum
            iv_tanum              = lv_tanum
            iv_nista              = lv_nista
            iv_altme              = lv_altme
            iv_nlpla              = lv_nlpla
            iv_nlenr              = lv_nlenr
            iv_parti              = lv_parti
            iv_rsrc               = lv_rsrc
            iv_conf_exc           = lv_conf_exc_str
          importing
            et_ltap_vb            = lt_ltap_vb
          exceptions
            wht_not_confirmed     = 1
            wht_already_confirmed = 2
            internal_error        = 3
            others                = 4.
        case sy-subrc.
          when 0.
            move-corresponding lt_ltap_vb to lt_warehousetaskconf.
            copy_data_to_ref( exporting is_data = lt_warehousetaskconf
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wnc
                message          = text-017.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wac
                message          = text-023.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'ConfirmWarehouseTaskFirstStep'.

        call function 'ZCONFIRM_WAREHOUSE_TASK_STEP_1'
          exporting
            iv_lgnum              = lv_lgnum
            iv_tanum              = lv_tanum
            iv_rsrc               = lv_rsrc
          importing
            et_ltap_vb            = lt_ltap_vb
          exceptions
            wht_not_confirmed     = 1
            wht_already_confirmed = 2
            internal_error        = 3
            others                = 4.
        case sy-subrc.
          when 0.
            move-corresponding lt_ltap_vb to lt_warehousetaskconf.
            copy_data_to_ref( exporting is_data = lt_warehousetaskconf
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wnc
                message          = text-017.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wac
                message          = text-023.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'UnassignRobotFromWarehouseOrder'.
        call function 'ZUNASSIGN_ROBOT_WHO'
          exporting
            iv_lgnum           = lv_lgnum
            iv_rsrc            = lv_rsrc
            iv_who             = lv_who
          importing
            es_who             = ls_who
          exceptions
            robot_not_found    = 1
            who_not_found      = 2
            who_locked         = 3
            who_in_process     = 4
            who_not_unassigned = 5
            internal_error     = 6
            others             = 7.
        case sy-subrc.
          when 0.
            move-corresponding ls_who to ls_warehouseorder.
            copy_data_to_ref( exporting is_data = ls_warehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnf
                message          = text-001.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 3.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wol
                message          = text-010.
          when 4.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wip
                message          = text-019.
          when 5.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wnu
                message          = text-020.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'UnsetWarehouseorderInProcessStatus'.
        call function 'ZUNSET_WHO_IN_PROCESS_STATUS'
          exporting
            iv_lgnum               = lv_lgnum
            iv_who                 = lv_who
          importing
            es_who                 = ls_who
          exceptions
            who_not_found          = 1
            who_locked             = 2
            who_status_not_updated = 3
            internal_error         = 4
            others                 = 5.
        case sy-subrc.
          when 0.
            move-corresponding ls_who to ls_warehouseorder.
            copy_data_to_ref( exporting is_data = ls_warehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wol
                message          = text-010.
          when 3.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wsn
                message          = text-024.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'SendFirstConfirmationError'.

        call function 'ZSEND_FIRST_CONF_ERROR'
          exporting
            iv_lgnum           = lv_lgnum
            iv_rsrc            = lv_rsrc
            iv_who             = lv_who
            iv_tanum           = lv_tanum
          importing
            es_who             = ls_who
          exceptions
            robot_not_found    = 1
            who_not_found      = 2
            who_locked         = 3
            who_in_process     = 4
            who_not_unassigned = 5
            no_error_queue     = 6
            queue_not_changed  = 7
            internal_error     = 8
            others             = 9.
        case sy-subrc.
          when 0.
            move-corresponding ls_who to ls_warehouseorder.
            copy_data_to_ref( exporting is_data = ls_warehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnf
                message          = text-001.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 3.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wol
                message          = text-010.
          when 4.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wip
                message          = text-019.
          when 5.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wnu
                message          = text-020.
          when 6.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_neq
                message          = text-021.
          when 7.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_qnc
                message          = text-022.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.

      when 'SendSecondConfirmationError'.

        call function 'ZSEND_SECOND_CONF_ERROR'
          exporting
            iv_lgnum          = lv_lgnum
            iv_rsrc           = lv_rsrc
            iv_who            = lv_who
            iv_tanum          = lv_tanum
          importing
            es_who            = ls_who
          exceptions
            robot_not_found   = 1
            who_not_found     = 2
            who_locked        = 3
            no_error_queue    = 4
            queue_not_changed = 5
            internal_error    = 6
            others            = 7.
        case sy-subrc.
          when 0.
            move-corresponding ls_who to ls_warehouseorder.
            copy_data_to_ref( exporting is_data = ls_warehouseorder
              changing cr_data = er_data ).
          when 1.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_rnf
                message          = text-001.
          when 2.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_nof
                message          = text-002.
          when 3.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_wol
                message          = text-010.
          when 4.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_neq
                message          = text-021.
          when 5.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_qnc
                message          = text-022.
          when others.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid           = /iwbep/cx_mgw_busi_exception=>business_error
                http_status_code = 404
                msg_code         = gc_error_ie
                message          = text-003.
        endcase.  "case sy-subrc.


    endcase.  "case lv_action_name.

  endmethod.


  method openwarehousetas_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum         type /scwm/lgnum,
          lv_tanum         type /scwm/tanum,
          ls_warehousetask type zcl_zewm_robco_mpc=>ts_openwarehousetask.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'Tanum'.
          lv_tanum = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/ordim_o into corresponding fields of @ls_warehousetask
        where lgnum = @lv_lgnum and
              tanum = @lv_tanum.

    if sy-subrc = 0.
      er_entity = ls_warehousetask.
    endif.
  endmethod.


  method openwarehousetas_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum         type /scwm/lgnum,
          lv_who           type /scwm/de_who,
          lt_warehousetask type zcl_zewm_robco_mpc=>tt_openwarehousetask.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'Who'.
          lv_who = <ls_key>-value.
      endcase.
    endloop.

    if lv_lgnum is not initial.
      select * from /scwm/ordim_o into corresponding fields of table @lt_warehousetask
          where lgnum = @lv_lgnum and
                who = @lv_who.
      if sy-subrc = 0.
* When expanding open warehouse task from warehouse order, use the same sort as in RF function /SCWM/RF_PICK_WHO_TO_SORT
        sort lt_warehousetask ascending by lgnum whoseq pathseq tanum.
        et_entityset = lt_warehousetask.
      endif.
    else.
      select * from /scwm/ordim_o into corresponding fields of table @lt_warehousetask.
      if sy-subrc = 0.
        et_entityset = lt_warehousetask.
      endif.
    endif.

    if et_entityset is not initial.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if et_entityset is not initial.

  endmethod.


  method resourcegroupdes_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum      type /scwm/lgnum,
          lv_langu      type spras,
          lv_rsrc_grp   type /scwm/de_rsrc_grp,
          ls_trsrc_grpt type zcl_zewm_robco_mpc=>ts_resourcegroupdescription.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'RsrcGrp'.
          lv_rsrc_grp = <ls_key>-value.
        when 'Langu'.
          lv_langu = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/trsrc_grpt
      into corresponding fields of @ls_trsrc_grpt
        where lgnum = @lv_lgnum
          and rsrc_grp = @lv_rsrc_grp
          and langu = @lv_langu.
    if sy-subrc = 0.
      er_entity = ls_trsrc_grpt.
    endif.

  endmethod.


  method resourcegroupdes_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: s_lgnum       type range of /scwm/lgnum,
          s_rsrc_grp    type range of /scwm/de_rsrc_grp,
          ls_selopt     type /iwbep/s_cod_select_option,
          lt_selopt     type /iwbep/t_cod_select_options,
          lt_trsrc_grpt type zcl_zewm_robco_mpc=>tt_resourcegroupdescription.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    data(lv_where) = io_tech_request_context->get_osql_where_clause_convert( ).

* OData keys from associations
    loop at it_key_tab assigning <ls_key>.
      clear: ls_selopt, lt_selopt.
      ls_selopt-sign = 'I'.
      ls_selopt-option = 'EQ'.
      case <ls_key>-name.
        when 'Lgnum'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_lgnum[].
        when 'RsrcGrp'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_rsrc_grp[].
      endcase.
    endloop.

    if lv_where is not initial.
      lv_where = lv_where && ' and lgnum in @s_lgnum and rsrc_grp in @s_rsrc_grp and langu = @sy-langu'.
      select * from /scwm/trsrc_grpt
        into corresponding fields of table @lt_trsrc_grpt
        where (lv_where).
    else.
      select * from /scwm/trsrc_grpt
        into corresponding fields of table @lt_trsrc_grpt
        where lgnum in @s_lgnum
          and rsrc_grp in @s_rsrc_grp
          and langu = @sy-langu.
    endif.  "if lv_where is not initial.

    if sy-subrc = 0.
      et_entityset = lt_trsrc_grpt.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method resourcegroupset_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum     type /scwm/lgnum,
          lv_spras     type spras,
          lv_rsrc_grp  type /scwm/de_rsrc_grp,
          ls_trsrc_grp type zcl_zewm_robco_mpc=>ts_resourcegroup.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'RsrcGrp'.
          lv_rsrc_grp = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/trsrc_grp
      into corresponding fields of @ls_trsrc_grp
        where lgnum = @lv_lgnum
          and rsrc_grp = @lv_rsrc_grp.
    if sy-subrc = 0.
      er_entity = ls_trsrc_grp.
    endif.

  endmethod.


  method resourcegroupset_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: s_lgnum      type range of /scwm/lgnum,
          ls_selopt    type /iwbep/s_cod_select_option,
          lt_selopt    type /iwbep/t_cod_select_options,
          lt_trsrc_grp type zcl_zewm_robco_mpc=>tt_resourcegroup.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

* OData keys from associations
    loop at it_key_tab assigning <ls_key>.
      clear: ls_selopt, lt_selopt.
      ls_selopt-sign = 'I'.
      ls_selopt-option = 'EQ'.
      case <ls_key>-name.
        when 'Lgnum'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_lgnum[].
      endcase.
    endloop.

    select * from /scwm/trsrc_grp
      into corresponding fields of table @lt_trsrc_grp
      where lgnum in @s_lgnum.

    if sy-subrc = 0.
      et_entityset = lt_trsrc_grp.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method resourcetypedesc_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum      type /scwm/lgnum,
          lv_langu      type spras,
          lv_rsrc_type  type /scwm/de_rsrc_type,
          ls_trsrc_typt type zcl_zewm_robco_mpc=>ts_resourcetypedescription.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'RsrcType'.
          lv_rsrc_type = <ls_key>-value.
        when 'Langu'.
          lv_langu = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/trsrc_typt
      into corresponding fields of @ls_trsrc_typt
        where lgnum = @lv_lgnum
          and rsrc_type = @lv_rsrc_type
          and langu = @lv_langu.
    if sy-subrc = 0.
      er_entity = ls_trsrc_typt.
    endif.

  endmethod.


  method resourcetypedesc_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: s_lgnum       type range of /scwm/lgnum,
          s_rsrc_type   type range of /scwm/de_rsrc_grp,
          ls_selopt     type /iwbep/s_cod_select_option,
          lt_selopt     type /iwbep/t_cod_select_options,
          lt_trsrc_typt type zcl_zewm_robco_mpc=>tt_resourcetypedescription.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    data(lv_where) = io_tech_request_context->get_osql_where_clause_convert( ).

* OData keys from associations
    loop at it_key_tab assigning <ls_key>.
      clear: ls_selopt, lt_selopt.
      ls_selopt-sign = 'I'.
      ls_selopt-option = 'EQ'.
      case <ls_key>-name.
        when 'Lgnum'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_lgnum[].
        when 'RsrcType'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_rsrc_type[].
      endcase.
    endloop.

    if lv_where is not initial.
      lv_where = lv_where && ' and lgnum in @s_lgnum and rsrc_type in @s_rsrc_type and langu = @sy-langu'.
      select * from /scwm/trsrc_typt
        into corresponding fields of table @lt_trsrc_typt
        where (lv_where).
    else.
      select * from /scwm/trsrc_typt
        into corresponding fields of table @lt_trsrc_typt
        where lgnum in @s_lgnum and rsrc_type in @s_rsrc_type and langu = @sy-langu.
    endif.  "if lv_where is not initial.

    if sy-subrc = 0.
      et_entityset = lt_trsrc_typt.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method robotresourcetyp_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum             type /scwm/lgnum,
          lv_spras             type spras,
          lv_rsrc_type         type /scwm/de_rsrc_type,
          ls_robotresourcetype type zcl_zewm_robco_mpc=>ts_robotresourcetype.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'RsrcType'.
          lv_rsrc_type = <ls_key>-value.
      endcase.
    endloop.

    select single * from zewm_trsrc_typ
      into corresponding fields of @ls_robotresourcetype
        where lgnum = @lv_lgnum
          and rsrc_type = @lv_rsrc_type.
    if sy-subrc = 0.
      er_entity = ls_robotresourcetype.
    endif.

  endmethod.


  method robotresourcetyp_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: s_lgnum              type range of /scwm/lgnum,
          ls_selopt            type /iwbep/s_cod_select_option,
          lt_selopt            type /iwbep/t_cod_select_options,
          lt_robotresourcetype type zcl_zewm_robco_mpc=>tt_robotresourcetype.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

* OData keys from associations
    loop at it_key_tab assigning <ls_key>.
      clear: ls_selopt, lt_selopt.
      ls_selopt-sign = 'I'.
      ls_selopt-option = 'EQ'.
      case <ls_key>-name.
        when 'Lgnum'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_lgnum[].
      endcase.
    endloop.

    select * from zewm_trsrc_typ
      into corresponding fields of table @lt_robotresourcetype
      where lgnum in @s_lgnum.

    if sy-subrc = 0.
      et_entityset =  lt_robotresourcetype.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method robotset_create_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: ls_zewm_trsrc_typ type zewm_trsrc_typ,
          ls_robot_input    type zcl_zewm_robco_mpc=>ts_robot,
          ls_rsrc_v         type /scwm/v_rsrc,
          ls_trsrc_grp      type /scwm/trsrc_grp.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '01'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

* Get data from oData service
    io_data_provider->read_entry_data( importing es_data = ls_robot_input ).

* Check if valid Resource Type is provided
    if ls_robot_input-rsrc_type is initial.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_nrt
          message  = text-005.
    else.
      select single * from zewm_trsrc_typ into @ls_zewm_trsrc_typ
        where lgnum = @ls_robot_input-lgnum
          and rsrc_type = @ls_robot_input-rsrc_type.
      if sy-subrc <> 0.
        raise exception type /iwbep/cx_mgw_busi_exception
          exporting
            textid   = /iwbep/cx_mgw_busi_exception=>business_error
            msg_code = gc_error_rnr
            message  = text-008.
      endif.
    endif.

* Check if valid Resource Group is provided
    if ls_robot_input-rsrc_grp is initial.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_nrg
          message  = text-006.
    else.
      select single * from /scwm/trsrc_grp into @ls_trsrc_grp
        where lgnum = @ls_robot_input-lgnum
          and rsrc_grp = @ls_robot_input-rsrc_grp.
      if sy-subrc <> 0.
        raise exception type /iwbep/cx_mgw_busi_exception
          exporting
            textid   = /iwbep/cx_mgw_busi_exception=>business_error
            msg_code = gc_error_rne
            message  = text-013.
      endif.
    endif.

* Copy resource data from oData input
    ls_rsrc_v-lgnum = ls_robot_input-lgnum.
    ls_rsrc_v-rsrc = ls_robot_input-rsrc.
    ls_rsrc_v-rsrc_type = ls_robot_input-rsrc_type.
    ls_rsrc_v-rsrc_grp = ls_robot_input-rsrc_grp.

    call function 'VIEW_MAINTENANCE_SINGLE_ENTRY'
      exporting
        action                       = 'INS'
        view_name                    = '/scwm/v_rsrc'
        no_transport                 = 'X'
        suppressdialog               = 'X'
      changing
        entry                        = ls_rsrc_v
      exceptions
        entry_already_exists         = 1
        entry_not_found              = 2
        client_reference             = 3
        foreign_lock                 = 4
        invalid_action               = 5
        no_clientindependent_auth    = 6
        no_database_function         = 7
        no_editor_function           = 8
        no_show_auth                 = 9
        no_tvdir_entry               = 10
        no_upd_auth                  = 11
        system_failure               = 12
        unknown_field_in_dba_sellist = 13
        view_not_found               = 14
        others                       = 15.
    if sy-subrc = 0.
* Prepare Output
      move-corresponding ls_rsrc_v to er_entity.
    elseif sy-subrc = 1.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_rae
          message  = text-007.
    else.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_ie
          message  = text-003.
    endif.

  endmethod.


  method robotset_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum type /scwm/lgnum,
          lv_rsrc  type /scwm/de_rsrc,
          ls_robot type zcl_zewm_robco_mpc=>ts_robot.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'Rsrc'.
          lv_rsrc = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/rsrc as r
      inner join zewm_trsrc_typ as z
        on r~lgnum = z~lgnum
          and r~rsrc_type = z~rsrc_type
      into corresponding fields of @ls_robot
        where r~lgnum = @lv_lgnum
          and r~rsrc = @lv_rsrc.
    if sy-subrc = 0.
      er_entity = ls_robot.
    endif.

  endmethod.


  method robotset_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: s_lgnum     type range of /scwm/lgnum,
          s_rsrc_type type range of /scwm/rsrc-rsrc_type,
          s_rsrc_grp  type range of /scwm/rsrc-rsrc_grp,
          ls_selopt   type /iwbep/s_cod_select_option,
          lt_selopt   type /iwbep/t_cod_select_options,
          lt_robot    type zcl_zewm_robco_mpc=>tt_robot.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

* OData keys from associations
    loop at it_key_tab assigning <ls_key>.
      clear: ls_selopt, lt_selopt.
      ls_selopt-sign = 'I'.
      ls_selopt-option = 'EQ'.
      case <ls_key>-name.
        when 'Lgnum'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_lgnum[].
        when 'RsrcType'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_rsrc_type[].
        when 'RsrcGrp'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_rsrc_grp[].
      endcase.
    endloop.

    select * from /scwm/rsrc as r
      inner join zewm_trsrc_typ as z
        on r~lgnum = z~lgnum
          and r~rsrc_type = z~rsrc_type
      into corresponding fields of table @lt_robot
      where r~lgnum in @s_lgnum
        and r~rsrc_type in @s_rsrc_type
        and r~rsrc_grp in @s_rsrc_grp.

    if sy-subrc = 0.
      et_entityset = lt_robot.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method robotset_update_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: ls_zewm_trsrc_typ type zewm_trsrc_typ,
          ls_robot_input    type zcl_zewm_robco_mpc=>ts_robot,
          ls_rsrc           type /scwm/rsrc,
          ls_rsrc_v         type /scwm/v_rsrc,
          ls_trsrc_grp      type /scwm/trsrc_grp.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '02'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

* Get data from oData service
    io_data_provider->read_entry_data( importing es_data = ls_robot_input ).

* Get Parameters of PUT request
    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
* Check if URI parameters and HTTP body values are consistant
          if <ls_key>-value <> ls_robot_input-lgnum and ls_robot_input-lgnum is not initial.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid   = /iwbep/cx_mgw_busi_exception=>business_error
                msg_code = gc_error_ubi
                message  = text-016.
          else.
            ls_robot_input-lgnum = <ls_key>-value.
          endif.
        when 'Rsrc'.
* Check if URI parameters and HTTP body values are consistant
          if <ls_key>-value <> ls_robot_input-rsrc and ls_robot_input-rsrc is not initial.
            raise exception type /iwbep/cx_mgw_busi_exception
              exporting
                textid   = /iwbep/cx_mgw_busi_exception=>business_error
                msg_code = gc_error_ubi
                message  = text-016.
          else.
            ls_robot_input-rsrc = <ls_key>-value.
          endif.
      endcase.
    endloop.

* Check if valid Resource Type is provided
    if ls_robot_input-rsrc_type is initial.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_nrt
          message  = text-005.
    else.
      select single * from zewm_trsrc_typ into @ls_zewm_trsrc_typ
        where lgnum = @ls_robot_input-lgnum
          and rsrc_type = @ls_robot_input-rsrc_type.
      if sy-subrc <> 0.
        raise exception type /iwbep/cx_mgw_busi_exception
          exporting
            textid   = /iwbep/cx_mgw_busi_exception=>business_error
            msg_code = gc_error_rnr
            message  = text-008.
      endif.
    endif.

* Check if valid Resource Group is provided
    if ls_robot_input-rsrc_grp is initial.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_nrg
          message  = text-006.
    else.
      select single * from /scwm/trsrc_grp into @ls_trsrc_grp
        where lgnum = @ls_robot_input-lgnum
          and rsrc_grp = @ls_robot_input-rsrc_grp.
      if sy-subrc <> 0.
        raise exception type /iwbep/cx_mgw_busi_exception
          exporting
            textid   = /iwbep/cx_mgw_busi_exception=>business_error
            msg_code = gc_error_rne
            message  = text-013.
      endif.
    endif.

* Get resource dataset
    call function '/SCWM/RSRC_READ_SINGLE'
      exporting
        iv_lgnum    = ls_robot_input-lgnum
        iv_rsrc     = ls_robot_input-rsrc
        iv_db_lock  = abap_true
      importing
        es_rsrc     = ls_rsrc
      exceptions
        wrong_input = 1
        not_found   = 2
        others      = 3.
    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_rnf
          message  = text-001.
    endif.

* Update resource data from oData input
    ls_rsrc-rsrc_type = ls_robot_input-rsrc_type.
    ls_rsrc-rsrc_grp = ls_robot_input-rsrc_grp.

* Update entry
    move-corresponding ls_rsrc to ls_rsrc_v.
    call function 'VIEW_MAINTENANCE_SINGLE_ENTRY'
      exporting
        action                       = 'UPD'
        view_name                    = '/scwm/v_rsrc'
        no_transport                 = 'X'
        suppressdialog               = 'X'
      changing
        entry                        = ls_rsrc_v
      exceptions
        entry_already_exists         = 1
        entry_not_found              = 2
        client_reference             = 3
        foreign_lock                 = 4
        invalid_action               = 5
        no_clientindependent_auth    = 6
        no_database_function         = 7
        no_editor_function           = 8
        no_show_auth                 = 9
        no_tvdir_entry               = 10
        no_upd_auth                  = 11
        system_failure               = 12
        unknown_field_in_dba_sellist = 13
        view_not_found               = 14
        others                       = 15.
    if sy-subrc = 0.
* Prepare Output
      move-corresponding ls_rsrc_v to er_entity.
    elseif sy-subrc = 2.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_rnf
          message  = text-001.
    elseif sy-subrc = 4.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_flk
          message  = text-025.
    else.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid   = /iwbep/cx_mgw_busi_exception=>business_error
          msg_code = gc_error_ie
          message  = text-003.
    endif.

  endmethod.


  method storagebinset_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum      type /scwm/lgnum,
          lv_lgpla      type /scwm/lgpla,
          ls_storagebin type zcl_zewm_robco_mpc=>ts_storagebin.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'Lgpla'.
          lv_lgpla = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/lagp into corresponding fields of @ls_storagebin
        where lgnum = @lv_lgnum
          and lgpla = @lv_lgpla.
    if sy-subrc = 0.
      er_entity = ls_storagebin.
    endif.

  endmethod.


  method storagebinset_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum      type /scwm/lgnum,
          lt_storagebin type zcl_zewm_robco_mpc=>tt_storagebin.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
      endcase.
    endloop.

    if lv_lgnum is not initial.
      select * from /scwm/lagp into corresponding fields of table @lt_storagebin
        where lgnum = @lv_lgnum.
    else.
      select * from /scwm/lagp into corresponding fields of table @lt_storagebin.
    endif.  "if lv_lgnum is not initial.

    if sy-subrc = 0.
      et_entityset = lt_storagebin.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method warehousedescrip_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum                type /scwm/lgnum,
          lv_spras                type spras,
          ls_warehousedescription type zcl_zewm_robco_mpc=>ts_warehousedescription.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'Spras'.
          lv_spras = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/t300t into corresponding fields of @ls_warehousedescription
        where lgnum = @lv_lgnum
          and spras = @lv_spras.
    if sy-subrc = 0.
      er_entity = ls_warehousedescription.
    endif.

  endmethod.


  method warehousedescrip_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum                type /scwm/lgnum,
          lt_warehousedescription type zcl_zewm_robco_mpc=>tt_warehousedescription.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    data(lv_where) = io_tech_request_context->get_osql_where_clause_convert( ).

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
      endcase.
    endloop.

    if lv_lgnum is not initial.
      if lv_where is not initial.
        lv_where = 'lgnum = @lv_lgnum and ' && lv_where.
        select * from /scwm/t300t into corresponding fields of table @lt_warehousedescription
          where (lv_where).
      else.
        select * from /scwm/t300t into corresponding fields of table @lt_warehousedescription
          where lgnum = @lv_lgnum.
      endif.  "if lv_where is not initial.
    else.
      if lv_where is not initial.
        select * from /scwm/t300t into corresponding fields of table @lt_warehousedescription where (lv_where).
      else.
        select * from /scwm/t300t into corresponding fields of table @lt_warehousedescription.
      endif.  "if lv_where is not initial.
    endif.  "if lv_lgnum is not initial.

    if sy-subrc = 0.
      et_entityset = lt_warehousedescription.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method warehousenumbers_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum           type /scwm/lgnum,
          ls_warehousenumber type zcl_zewm_robco_mpc=>ts_warehousenumber.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/t300 into corresponding fields of @ls_warehousenumber
        where lgnum = @lv_lgnum.
    if sy-subrc = 0.
      er_entity = ls_warehousenumber.
    endif.

  endmethod.


  method warehousenumbers_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lt_warehousenumber type zcl_zewm_robco_mpc=>tt_warehousenumber.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    select * from /scwm/t300 into corresponding fields of table @lt_warehousenumber.
    if sy-subrc = 0.
      et_entityset = lt_warehousenumber.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.


  method warehouseorderse_get_entity.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lv_lgnum          type /scwm/lgnum,
          lv_who            type /scwm/de_who,
          ls_warehouseorder type zcl_zewm_robco_mpc=>ts_warehouseorder.

    field-symbols: <ls_key> like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

    loop at it_key_tab assigning <ls_key>.
      case <ls_key>-name.
        when 'Lgnum'.
          lv_lgnum = <ls_key>-value.
        when 'Who'.
          lv_who = <ls_key>-value.
      endcase.
    endloop.

    select single * from /scwm/who into corresponding fields of @ls_warehouseorder
        where lgnum = @lv_lgnum
          and who = @lv_who.
    if sy-subrc = 0.
      er_entity = ls_warehouseorder.
    endif.

  endmethod.


  method warehouseorderse_get_entityset.
**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**

    data: lt_filter         type /iwbep/t_mgw_select_option,
          lt_warehouseorder type zcl_zewm_robco_mpc=>tt_warehouseorder,
          ls_selopt         type /iwbep/s_cod_select_option,
          lt_selopt         type /iwbep/t_cod_select_options,
          s_lgnum           type range of /scwm/lgnum,
          s_rsrc            type range of /scwm/who-rsrc,
          s_status          type range of /scwm/who-status,
          s_topwhoid        type range of /scwm/who-topwhoid.

    field-symbols: <ls_filter> type /iwbep/s_mgw_select_option,
                   <ls_key>    like line of it_key_tab.

    authority-check object 'ZEWM_ROBCO'
      id 'ACTVT'  field '03'.

    if sy-subrc <> 0.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid           = /iwbep/cx_mgw_busi_exception=>business_error
          http_status_code = 401
          msg_code         = gc_error_noa
          message          = text-026.
    endif.

* OData filters
    lt_filter = io_tech_request_context->get_filter( )->get_filter_select_options( ).
    loop at lt_filter assigning <ls_filter>.
      if <ls_filter>-property = 'LGNUM'.
        move-corresponding <ls_filter>-select_options[] to s_lgnum[] keeping target lines.
      elseif <ls_filter>-property = 'RSRC'.
        move-corresponding <ls_filter>-select_options[] to s_rsrc[] keeping target lines.
      elseif <ls_filter>-property = 'STATUS'.
        move-corresponding <ls_filter>-select_options[] to s_status[] keeping target lines.
      elseif <ls_filter>-property = 'TOPWHOID'.
        move-corresponding <ls_filter>-select_options[] to s_topwhoid[] keeping target lines.
      endif.
    endloop.

* OData keys from associations
* If there are keys from OData associations, overwrite corresponding filters
    loop at it_key_tab assigning <ls_key>.
      clear: ls_selopt, lt_selopt.
      ls_selopt-sign = 'I'.
      ls_selopt-option = 'EQ'.
      case <ls_key>-name.
        when 'Lgnum'.
          ls_selopt-low = <ls_key>-value.
          append ls_selopt to lt_selopt.
          move-corresponding lt_selopt[] to s_lgnum[].
      endcase.
    endloop.

* Select from database
    select * from /scwm/who into corresponding fields of table @lt_warehouseorder
        where lgnum in @s_lgnum
          and rsrc in @s_rsrc
          and status in @s_status
          and topwhoid in @s_topwhoid.

    if sy-subrc = 0.
      et_entityset = lt_warehouseorder.

* Apply $inlinecount query option
      if io_tech_request_context->has_inlinecount( ) = abap_true.
        describe table et_entityset lines es_response_context-inlinecount.
      else.
        clear es_response_context-inlinecount.
      endif.

* Apply $filter query option
      call method /iwbep/cl_mgw_data_util=>filtering
        exporting
          it_select_options = it_filter_select_options
        changing
          ct_data           = et_entityset.

* Apply $top and $skip query options
      call method /iwbep/cl_mgw_data_util=>paging
        exporting
          is_paging = is_paging
        changing
          ct_data   = et_entityset.

* Apply $orderby query option
      call method /iwbep/cl_mgw_data_util=>orderby
        exporting
          it_order = it_order
        changing
          ct_data  = et_entityset.

    endif.  " if sy-subrc = 0.

  endmethod.
ENDCLASS.
