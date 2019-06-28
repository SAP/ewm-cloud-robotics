class ZCL_ZEWM_ROBCO_MPC definition
  public
  inheriting from /IWBEP/CL_MGW_PUSH_ABS_MODEL
  create public .

public section.

  types:
          NEWWAREHOUSEORDER type /SCWM/WHO .
  types:
       begin of ts_text_element,
      artifact_name  type c length 40,       " technical name
      artifact_type  type c length 4,
      parent_artifact_name type c length 40, " technical name
      parent_artifact_type type c length 4,
      text_symbol    type textpoolky,
   end of ts_text_element .
  types:
             tt_text_elements type standard table of ts_text_element with key text_symbol .
  types:
          WAREHOUSETASKCONFIRMATION type /SCWM/LTAP .
  types:
        begin of TS_GETNEWROBOTWAREHOUSEORDER,
        RSRC type C length 18,
        LGNUM type C length 4,
    end of TS_GETNEWROBOTWAREHOUSEORDER .
  types:
        begin of TS_SETROBOTSTATUS,
        EXCCODE type C length 4,
        RSRC type C length 18,
        LGNUM type C length 4,
    end of TS_SETROBOTSTATUS .
  types:
        begin of TS_GETROBOTWAREHOUSEORDERS,
        RSRC type C length 18,
        LGNUM type C length 4,
    end of TS_GETROBOTWAREHOUSEORDERS .
  types:
        begin of TS_CONFIRMWAREHOUSETASKFIRSTST,
        RSRC type C length 18,
        LGNUM type C length 4,
        TANUM type C length 12,
    end of TS_CONFIRMWAREHOUSETASKFIRSTST .
  types:
        begin of TS_GETNEWROBOTTYPEWAREHOUSEORD,
        NO_WHO type /IWBEP/SB_ODATA_TY_INT2,
        LGNUM type C length 4,
        RSRC_GRP type C length 4,
        RSRC_TYPE type C length 4,
    end of TS_GETNEWROBOTTYPEWAREHOUSEORD .
  types:
        begin of TS_UNASSIGNROBOTFROMWAREHOUSEO,
        WHO type C length 10,
        RSRC type C length 18,
        LGNUM type C length 4,
    end of TS_UNASSIGNROBOTFROMWAREHOUSEO .
  types:
        begin of TS_SENDFIRSTCONFIRMATIONERROR,
        TANUM type C length 12,
        WHO type C length 10,
        RSRC type C length 18,
        LGNUM type C length 4,
    end of TS_SENDFIRSTCONFIRMATIONERROR .
  types:
        begin of TS_CONFIRMWAREHOUSETASK,
        LGNUM type C length 4,
        TANUM type C length 12,
        NISTA type P length 16 decimals 14,
        ALTME type C length 3,
        NLENR type C length 20,
        PARTI type FLAG,
        NLPLA type C length 18,
        CONF_EXC type C length 4,
    end of TS_CONFIRMWAREHOUSETASK .
  types:
        begin of TS_ASSIGNROBOTTOWAREHOUSEORDER,
        LGNUM type C length 4,
        RSRC type C length 18,
        WHO type C length 10,
    end of TS_ASSIGNROBOTTOWAREHOUSEORDER .
  types:
        begin of TS_SENDSECONDCONFIRMATIONERROR,
        LGNUM type C length 4,
        RSRC type C length 18,
        WHO type C length 10,
        TANUM type C length 12,
    end of TS_SENDSECONDCONFIRMATIONERROR .
  types:
         TS_WAREHOUSEORDER type /SCWM/WHO .
  types:
    TT_WAREHOUSEORDER type standard table of TS_WAREHOUSEORDER .
  types:
         TS_WAREHOUSENUMBER type /SCWM/T300 .
  types:
    TT_WAREHOUSENUMBER type standard table of TS_WAREHOUSENUMBER .
  types:
         TS_WAREHOUSEDESCRIPTION type /SCWM/T300T .
  types:
    TT_WAREHOUSEDESCRIPTION type standard table of TS_WAREHOUSEDESCRIPTION .
  types:
         TS_STORAGEBIN type /SCWM/LAGP .
  types:
    TT_STORAGEBIN type standard table of TS_STORAGEBIN .
  types:
         TS_ROBOT type /SCWM/RSRC .
  types:
    TT_ROBOT type standard table of TS_ROBOT .
  types:
         TS_OPENWAREHOUSETASK type /SCWM/ORDIM_O .
  types:
    TT_OPENWAREHOUSETASK type standard table of TS_OPENWAREHOUSETASK .

  constants GC_NEWWAREHOUSEORDER type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'NewWarehouseOrder' ##NO_TEXT.
  constants GC_OPENWAREHOUSETASK type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'OpenWarehouseTask' ##NO_TEXT.
  constants GC_ROBOT type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'Robot' ##NO_TEXT.
  constants GC_STORAGEBIN type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'StorageBin' ##NO_TEXT.
  constants GC_WAREHOUSEDESCRIPTION type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'WarehouseDescription' ##NO_TEXT.
  constants GC_WAREHOUSENUMBER type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'WarehouseNumber' ##NO_TEXT.
  constants GC_WAREHOUSEORDER type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'WarehouseOrder' ##NO_TEXT.
  constants GC_WAREHOUSETASKCONFIRMATION type /IWBEP/IF_MGW_MED_ODATA_TYPES=>TY_E_MED_ENTITY_NAME value 'WarehouseTaskConfirmation' ##NO_TEXT.

  methods LOAD_TEXT_ELEMENTS
  final
    returning
      value(RT_TEXT_ELEMENTS) type TT_TEXT_ELEMENTS
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .

  methods DEFINE
    redefinition .
  methods GET_LAST_MODIFIED
    redefinition .
protected section.
private section.

  constants GC_INCL_NAME type STRING value 'ZCL_ZEWM_ROBCO_MPC============CP' ##NO_TEXT.

  methods DEFINE_COMPLEXTYPES
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_WAREHOUSEORDER
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_WAREHOUSENUMBER
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_WAREHOUSEDESCRIPTION
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_STORAGEBIN
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_ROBOT
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_OPENWAREHOUSETASK
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_ASSOCIATIONS
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
  methods DEFINE_ACTIONS
    raising
      /IWBEP/CX_MGW_MED_EXCEPTION .
ENDCLASS.



CLASS ZCL_ZEWM_ROBCO_MPC IMPLEMENTATION.


  method DEFINE.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*

model->set_schema_namespace( 'ZEWM_ROBCO_SRV' ).

define_complextypes( ).
define_warehouseorder( ).
define_warehousenumber( ).
define_warehousedescription( ).
define_storagebin( ).
define_robot( ).
define_openwarehousetask( ).
define_associations( ).
define_actions( ).
  endmethod.


  method DEFINE_ACTIONS.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


data:
lo_action         type ref to /iwbep/if_mgw_odata_action,                 "#EC NEEDED
lo_parameter      type ref to /iwbep/if_mgw_odata_parameter.              "#EC NEEDED

***********************************************************************************************************************************
*   ACTION - GetNewRobotWarehouseOrder
***********************************************************************************************************************************

lo_action = model->create_action( 'GetNewRobotWarehouseOrder' ).  "#EC NOTEXT
*Set return complex type
lo_action->set_return_complex_type( 'NewWarehouseOrder' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'WarehouseOrder' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( '1' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '021' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '020' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_GETNEWROBOTWAREHOUSEORDER' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - SetRobotStatus
***********************************************************************************************************************************

lo_action = model->create_action( 'SetRobotStatus' ).  "#EC NOTEXT
*Set return entity type
lo_action->set_return_entity_type( 'Robot' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'Robot' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( '1' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Exccode'    iv_abap_fieldname = 'EXCCODE' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '008' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '009' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '010' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_SETROBOTSTATUS' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - GetRobotWarehouseOrders
***********************************************************************************************************************************

lo_action = model->create_action( 'GetRobotWarehouseOrders' ).  "#EC NOTEXT
*Set return entity type
lo_action->set_return_entity_type( 'WarehouseOrder' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'GET' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'WarehouseOrder' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( 'N' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '027' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '026' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_GETROBOTWAREHOUSEORDERS' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - ConfirmWarehouseTaskFirstStep
***********************************************************************************************************************************

lo_action = model->create_action( 'ConfirmWarehouseTaskFirstStep' ).  "#EC NOTEXT
*Set return complex type
lo_action->set_return_complex_type( 'WarehouseTaskConfirmation' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'OpenWarehouseTask' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( 'N' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '030' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '029' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Tanum'    iv_abap_fieldname = 'TANUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '028' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 12 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_CONFIRMWAREHOUSETASKFIRSTST' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - GetNewRobotTypeWarehouseOrders
***********************************************************************************************************************************

lo_action = model->create_action( 'GetNewRobotTypeWarehouseOrders' ).  "#EC NOTEXT
*Set return complex type
lo_action->set_return_complex_type( 'NewWarehouseOrder' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'WarehouseOrder' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( 'N' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'NoWho'    iv_abap_fieldname = 'NO_WHO' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '024' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_int16( ).
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '022' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'RsrcGrp'    iv_abap_fieldname = 'RSRC_GRP' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '031' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'RsrcType'    iv_abap_fieldname = 'RSRC_TYPE' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '025' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_GETNEWROBOTTYPEWAREHOUSEORD' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - UnassignRobotFromWarehouseorder
***********************************************************************************************************************************

lo_action = model->create_action( 'UnassignRobotFromWarehouseorder' ).  "#EC NOTEXT
*Set return entity type
lo_action->set_return_entity_type( 'WarehouseOrder' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'WarehouseOrder' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( '1' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Who'    iv_abap_fieldname = 'WHO' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '036' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '035' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '034' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_UNASSIGNROBOTFROMWAREHOUSEO' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - SendFirstConfirmationError
***********************************************************************************************************************************

lo_action = model->create_action( 'SendFirstConfirmationError' ).  "#EC NOTEXT
*Set return entity type
lo_action->set_return_entity_type( 'WarehouseOrder' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'WarehouseOrder' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( '1' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Tanum'    iv_abap_fieldname = 'TANUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '046' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 12 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Who'    iv_abap_fieldname = 'WHO' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '042' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '041' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '040' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_SENDFIRSTCONFIRMATIONERROR' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - ConfirmWarehouseTask
***********************************************************************************************************************************

lo_action = model->create_action( 'ConfirmWarehouseTask' ).  "#EC NOTEXT
*Set return complex type
lo_action->set_return_complex_type( 'WarehouseTaskConfirmation' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'OpenWarehouseTask' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( 'N' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '013' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Tanum'    iv_abap_fieldname = 'TANUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '012' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 12 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Nista'    iv_abap_fieldname = 'NISTA' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '011' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_decimal( ).
lo_parameter->set_precison( iv_precision = 14 ). "#EC NOTEXT
lo_parameter->set_maxlength( iv_max_length = 14 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Altme'    iv_abap_fieldname = 'ALTME' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '016' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 3 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Nlenr'    iv_abap_fieldname = 'NLENR' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '015' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 20 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Parti'    iv_abap_fieldname = 'PARTI' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '014' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_boolean( ).
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Nlpla'    iv_abap_fieldname = 'NLPLA' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '032' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'ConfExc'    iv_abap_fieldname = 'CONF_EXC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '033' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_CONFIRMWAREHOUSETASK' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - AssignRobotToWarehouseOrder
***********************************************************************************************************************************

lo_action = model->create_action( 'AssignRobotToWarehouseOrder' ).  "#EC NOTEXT
*Set return entity type
lo_action->set_return_entity_type( 'WarehouseOrder' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'WarehouseOrder' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( '1' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '019' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '018' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Who'    iv_abap_fieldname = 'WHO' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '017' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_ASSIGNROBOTTOWAREHOUSEORDER' ). "#EC NOTEXT
***********************************************************************************************************************************
*   ACTION - SendSecondConfirmationError
***********************************************************************************************************************************

lo_action = model->create_action( 'SendSecondConfirmationError' ).  "#EC NOTEXT
*Set return entity type
lo_action->set_return_entity_type( 'WarehouseOrder' ). "#EC NOTEXT
*Set HTTP method GET or POST
lo_action->set_http_method( 'POST' ). "#EC NOTEXT
*Set the action for entity
lo_action->set_action_for( 'WarehouseOrder' ).        "#EC NOTEXT
* Set return type multiplicity
lo_action->set_return_multiplicity( '1' ). "#EC NOTEXT
***********************************************************************************************************************************
* Parameters
***********************************************************************************************************************************

lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Lgnum'    iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '043' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Rsrc'    iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '044' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Who'    iv_abap_fieldname = 'WHO' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '045' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_parameter = lo_action->create_input_parameter( iv_parameter_name = 'Tanum'    iv_abap_fieldname = 'TANUM' ). "#EC NOTEXT
lo_parameter->set_label_from_text_element( iv_text_element_symbol = '047' iv_text_element_container = gc_incl_name ). "#EC NOTEXT
lo_parameter->/iwbep/if_mgw_odata_property~set_type_edm_string( ).
lo_parameter->set_maxlength( iv_max_length = 12 ). "#EC NOTEXT
lo_action->bind_input_structure( iv_structure_name  = 'ZCL_ZEWM_ROBCO_MPC=>TS_SENDSECONDCONFIRMATIONERROR' ). "#EC NOTEXT
  endmethod.


  method DEFINE_ASSOCIATIONS.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*




data:
lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,                   "#EC NEEDED
lo_entity_type    type ref to /iwbep/if_mgw_odata_entity_typ,                   "#EC NEEDED
lo_association    type ref to /iwbep/if_mgw_odata_assoc,                        "#EC NEEDED
lo_ref_constraint type ref to /iwbep/if_mgw_odata_ref_constr,                   "#EC NEEDED
lo_assoc_set      type ref to /iwbep/if_mgw_odata_assoc_set,                    "#EC NEEDED
lo_nav_property   type ref to /iwbep/if_mgw_odata_nav_prop.                     "#EC NEEDED

***********************************************************************************************************************************
*   ASSOCIATIONS
***********************************************************************************************************************************

 lo_association = model->create_association(
                            iv_association_name = 'WarehouseNumberToDescription' "#EC NOTEXT
                            iv_left_type        = 'WarehouseNumber' "#EC NOTEXT
                            iv_right_type       = 'WarehouseDescription' "#EC NOTEXT
                            iv_right_card       = 'N' "#EC NOTEXT
                            iv_left_card        = '1'  "#EC NOTEXT
                            iv_def_assoc_set    = abap_false ). "#EC NOTEXT
* Referential constraint for association - WarehouseNumberToDescription
lo_ref_constraint = lo_association->create_ref_constraint( ).
lo_ref_constraint->add_property( iv_principal_property = 'Lgnum'   iv_dependent_property = 'Lgnum' ). "#EC NOTEXT
lo_assoc_set = model->create_association_set( iv_association_set_name  = 'WarehouseNumberToDescriptionSet'                         "#EC NOTEXT
                                              iv_left_entity_set_name  = 'WarehouseNumberSet'              "#EC NOTEXT
                                              iv_right_entity_set_name = 'WarehouseDescriptionSet'             "#EC NOTEXT
                                              iv_association_name      = 'WarehouseNumberToDescription' ).                                 "#EC NOTEXT

 lo_association = model->create_association(
                            iv_association_name = 'WarehouseNumberToWarehouseOrder' "#EC NOTEXT
                            iv_left_type        = 'WarehouseNumber' "#EC NOTEXT
                            iv_right_type       = 'WarehouseOrder' "#EC NOTEXT
                            iv_right_card       = 'M' "#EC NOTEXT
                            iv_left_card        = '1'  "#EC NOTEXT
                            iv_def_assoc_set    = abap_false ). "#EC NOTEXT
* Referential constraint for association - WarehouseNumberToWarehouseOrder
lo_ref_constraint = lo_association->create_ref_constraint( ).
lo_ref_constraint->add_property( iv_principal_property = 'Lgnum'   iv_dependent_property = 'Lgnum' ). "#EC NOTEXT
lo_assoc_set = model->create_association_set( iv_association_set_name  = 'WarehouseNumberToWarehouseOrderSet'                         "#EC NOTEXT
                                              iv_left_entity_set_name  = 'WarehouseNumberSet'              "#EC NOTEXT
                                              iv_right_entity_set_name = 'WarehouseOrderSet'             "#EC NOTEXT
                                              iv_association_name      = 'WarehouseNumberToWarehouseOrder' ).                                 "#EC NOTEXT

 lo_association = model->create_association(
                            iv_association_name = 'WarehouseNumberToStorageBin' "#EC NOTEXT
                            iv_left_type        = 'WarehouseNumber' "#EC NOTEXT
                            iv_right_type       = 'StorageBin' "#EC NOTEXT
                            iv_right_card       = 'M' "#EC NOTEXT
                            iv_left_card        = '1'  "#EC NOTEXT
                            iv_def_assoc_set    = abap_false ). "#EC NOTEXT
* Referential constraint for association - WarehouseNumberToStorageBin
lo_ref_constraint = lo_association->create_ref_constraint( ).
lo_ref_constraint->add_property( iv_principal_property = 'Lgnum'   iv_dependent_property = 'Lgnum' ). "#EC NOTEXT
lo_assoc_set = model->create_association_set( iv_association_set_name  = 'WarehouseNumberToStorageBinSet'                         "#EC NOTEXT
                                              iv_left_entity_set_name  = 'WarehouseNumberSet'              "#EC NOTEXT
                                              iv_right_entity_set_name = 'StorageBinSet'             "#EC NOTEXT
                                              iv_association_name      = 'WarehouseNumberToStorageBin' ).                                 "#EC NOTEXT

 lo_association = model->create_association(
                            iv_association_name = 'WarehouseNumberToRobot' "#EC NOTEXT
                            iv_left_type        = 'WarehouseNumber' "#EC NOTEXT
                            iv_right_type       = 'Robot' "#EC NOTEXT
                            iv_right_card       = 'M' "#EC NOTEXT
                            iv_left_card        = '1'  "#EC NOTEXT
                            iv_def_assoc_set    = abap_false ). "#EC NOTEXT
* Referential constraint for association - WarehouseNumberToRobot
lo_ref_constraint = lo_association->create_ref_constraint( ).
lo_ref_constraint->add_property( iv_principal_property = 'Lgnum'   iv_dependent_property = 'Lgnum' ). "#EC NOTEXT
lo_assoc_set = model->create_association_set( iv_association_set_name  = 'WarehouseNumberToRobotSet'                         "#EC NOTEXT
                                              iv_left_entity_set_name  = 'WarehouseNumberSet'              "#EC NOTEXT
                                              iv_right_entity_set_name = 'RobotSet'             "#EC NOTEXT
                                              iv_association_name      = 'WarehouseNumberToRobot' ).                                 "#EC NOTEXT

 lo_association = model->create_association(
                            iv_association_name = 'WarehouseOrderToOpenWarehouseTask' "#EC NOTEXT
                            iv_left_type        = 'WarehouseOrder' "#EC NOTEXT
                            iv_right_type       = 'OpenWarehouseTask' "#EC NOTEXT
                            iv_right_card       = 'M' "#EC NOTEXT
                            iv_left_card        = '1'  "#EC NOTEXT
                            iv_def_assoc_set    = abap_false ). "#EC NOTEXT
* Referential constraint for association - WarehouseOrderToOpenWarehouseTask
lo_ref_constraint = lo_association->create_ref_constraint( ).
lo_ref_constraint->add_property( iv_principal_property = 'Lgnum'   iv_dependent_property = 'Lgnum' ). "#EC NOTEXT
lo_ref_constraint->add_property( iv_principal_property = 'Who'   iv_dependent_property = 'Who' ). "#EC NOTEXT
lo_assoc_set = model->create_association_set( iv_association_set_name  = 'WarehouseOrderToOpenWarehouseTaskSet'                         "#EC NOTEXT
                                              iv_left_entity_set_name  = 'WarehouseOrderSet'              "#EC NOTEXT
                                              iv_right_entity_set_name = 'OpenWarehouseTaskSet'             "#EC NOTEXT
                                              iv_association_name      = 'WarehouseOrderToOpenWarehouseTask' ).                                 "#EC NOTEXT


***********************************************************************************************************************************
*   NAVIGATION PROPERTIES
***********************************************************************************************************************************

* Navigation Properties for entity - WarehouseOrder
lo_entity_type = model->get_entity_type( iv_entity_name = 'WarehouseOrder' ). "#EC NOTEXT
lo_nav_property = lo_entity_type->create_navigation_property( iv_property_name  = 'OpenWarehouseTasks' "#EC NOTEXT
                                                              iv_abap_fieldname = 'OPENWAREHOUSEORDER' "#EC NOTEXT
                                                              iv_association_name = 'WarehouseOrderToOpenWarehouseTask' ). "#EC NOTEXT
* Navigation Properties for entity - WarehouseNumber
lo_entity_type = model->get_entity_type( iv_entity_name = 'WarehouseNumber' ). "#EC NOTEXT
lo_nav_property = lo_entity_type->create_navigation_property( iv_property_name  = 'WarehouseDescriptions' "#EC NOTEXT
                                                              iv_abap_fieldname = 'DESCRIPTION' "#EC NOTEXT
                                                              iv_association_name = 'WarehouseNumberToDescription' ). "#EC NOTEXT
lo_nav_property = lo_entity_type->create_navigation_property( iv_property_name  = 'WarehouseOrders' "#EC NOTEXT
                                                              iv_abap_fieldname = 'ORDER' "#EC NOTEXT
                                                              iv_association_name = 'WarehouseNumberToWarehouseOrder' ). "#EC NOTEXT
lo_nav_property = lo_entity_type->create_navigation_property( iv_property_name  = 'StorageBins' "#EC NOTEXT
                                                              iv_abap_fieldname = 'STORAGEBIN' "#EC NOTEXT
                                                              iv_association_name = 'WarehouseNumberToStorageBin' ). "#EC NOTEXT
lo_nav_property = lo_entity_type->create_navigation_property( iv_property_name  = 'Robots' "#EC NOTEXT
                                                              iv_abap_fieldname = 'ROBOT' "#EC NOTEXT
                                                              iv_association_name = 'WarehouseNumberToRobot' ). "#EC NOTEXT
  endmethod.


  method DEFINE_COMPLEXTYPES.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


 data:
       lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,             "#EC NEEDED
       lo_complex_type   type ref to /iwbep/if_mgw_odata_cmplx_type,             "#EC NEEDED
       lo_property       type ref to /iwbep/if_mgw_odata_property.                "#EC NEEDED

***********************************************************************************************************************************
*   COMPLEX TYPE - NewWarehouseOrder
***********************************************************************************************************************************
lo_complex_type = model->create_complex_type( 'NewWarehouseOrder' ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************
lo_property = lo_complex_type->create_property( iv_property_name  = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Who' iv_abap_fieldname = 'WHO' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ).
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Status' iv_abap_fieldname = 'STATUS' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 1 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Areawho' iv_abap_fieldname = 'AREAWHO' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Lgtyp' iv_abap_fieldname = 'LGTYP' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Lgpla' iv_abap_fieldname = 'LGPLA' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Queue' iv_abap_fieldname = 'QUEUE' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Rsrc' iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Lsd' iv_abap_fieldname = 'LSD' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_maxlength( iv_max_length = 15 ).
lo_property->set_conversion_exit( 'TSTWH' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Topwhoid' iv_abap_fieldname = 'TOPWHOID' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ).
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Refwhoid' iv_abap_fieldname = 'REFWHOID' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ).
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Flgwho' iv_abap_fieldname = 'FLGWHO' ). "#EC NOTEXT
lo_property->set_type_edm_boolean( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Flgto' iv_abap_fieldname = 'FLGTO' ). "#EC NOTEXT
lo_property->set_type_edm_boolean( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_complex_type->bind_structure( iv_structure_name   = '/SCWM/WHO'
                                 iv_bind_conversions = 'X' ). "#EC NOTEXT
***********************************************************************************************************************************
*   COMPLEX TYPE - WarehouseTaskConfirmation
***********************************************************************************************************************************
lo_complex_type = model->create_complex_type( 'WarehouseTaskConfirmation' ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************
lo_property = lo_complex_type->create_property( iv_property_name  = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Tanum' iv_abap_fieldname = 'TANUM' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 12 ).
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property = lo_complex_type->create_property( iv_property_name  = 'Tostat' iv_abap_fieldname = 'TOSTAT' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 1 ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_complex_type->bind_structure( iv_structure_name   = '/SCWM/LTAP'
                                 iv_bind_conversions = 'X' ). "#EC NOTEXT
  endmethod.


  method DEFINE_OPENWAREHOUSETASK.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


  data:
        lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,                "#EC NEEDED
        lo_entity_type    type ref to /iwbep/if_mgw_odata_entity_typ,                "#EC NEEDED
        lo_complex_type   type ref to /iwbep/if_mgw_odata_cmplx_type,                "#EC NEEDED
        lo_property       type ref to /iwbep/if_mgw_odata_property,                  "#EC NEEDED
        lo_entity_set     type ref to /iwbep/if_mgw_odata_entity_set.                "#EC NEEDED

***********************************************************************************************************************************
*   ENTITY - OpenWarehouseTask
***********************************************************************************************************************************

lo_entity_type = model->create_entity_type( iv_entity_type_name = 'OpenWarehouseTask' iv_def_entity_set = abap_false ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************

lo_property = lo_entity_type->create_property( iv_property_name = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Tanum' iv_abap_fieldname = 'TANUM' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 12 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Flghuto' iv_abap_fieldname = 'FLGHUTO' ). "#EC NOTEXT
lo_property->set_type_edm_boolean( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Tostat' iv_abap_fieldname = 'TOSTAT' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 1 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Priority' iv_abap_fieldname = 'PRIORITY' ). "#EC NOTEXT
lo_property->set_type_edm_byte( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Meins' iv_abap_fieldname = 'MEINS' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 3 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'CUNIT' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Vsolm' iv_abap_fieldname = 'VSOLM' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_precison( iv_precision = 14 ). "#EC NOTEXT
lo_property->set_maxlength( iv_max_length = 31 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Weight' iv_abap_fieldname = 'WEIGHT' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_precison( iv_precision = 3 ). "#EC NOTEXT
lo_property->set_maxlength( iv_max_length = 15 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'UnitW' iv_abap_fieldname = 'UNIT_W' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 3 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'CUNIT' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Volum' iv_abap_fieldname = 'VOLUM' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_precison( iv_precision = 3 ). "#EC NOTEXT
lo_property->set_maxlength( iv_max_length = 15 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'UnitV' iv_abap_fieldname = 'UNIT_V' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 3 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'CUNIT' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Vltyp' iv_abap_fieldname = 'VLTYP' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Vlber' iv_abap_fieldname = 'VLBER' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Vlpla' iv_abap_fieldname = 'VLPLA' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Vlenr' iv_abap_fieldname = 'VLENR' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 20 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'HUID' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Nltyp' iv_abap_fieldname = 'NLTYP' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Nlber' iv_abap_fieldname = 'NLBER' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Nlpla' iv_abap_fieldname = 'NLPLA' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Nlenr' iv_abap_fieldname = 'NLENR' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 20 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'HUID' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Who' iv_abap_fieldname = 'WHO' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).

lo_entity_type->bind_structure( iv_structure_name   = '/SCWM/ORDIM_O'
                                iv_bind_conversions = 'X' ). "#EC NOTEXT


***********************************************************************************************************************************
*   ENTITY SETS
***********************************************************************************************************************************
lo_entity_set = lo_entity_type->create_entity_set( 'OpenWarehouseTaskSet' ). "#EC NOTEXT

lo_entity_set->set_creatable( abap_false ).
lo_entity_set->set_updatable( abap_false ).
lo_entity_set->set_deletable( abap_false ).

lo_entity_set->set_pageable( abap_false ).
lo_entity_set->set_addressable( abap_true ).
lo_entity_set->set_has_ftxt_search( abap_false ).
lo_entity_set->set_subscribable( abap_false ).
lo_entity_set->set_filter_required( abap_false ).
  endmethod.


  method DEFINE_ROBOT.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


  data:
        lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,                "#EC NEEDED
        lo_entity_type    type ref to /iwbep/if_mgw_odata_entity_typ,                "#EC NEEDED
        lo_complex_type   type ref to /iwbep/if_mgw_odata_cmplx_type,                "#EC NEEDED
        lo_property       type ref to /iwbep/if_mgw_odata_property,                  "#EC NEEDED
        lo_entity_set     type ref to /iwbep/if_mgw_odata_entity_set.                "#EC NEEDED

***********************************************************************************************************************************
*   ENTITY - Robot
***********************************************************************************************************************************

lo_entity_type = model->create_entity_type( iv_entity_type_name = 'Robot' iv_def_entity_set = abap_false ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************

lo_property = lo_entity_type->create_property( iv_property_name = 'ActualBin' iv_abap_fieldname = 'ACTUAL_BIN' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'ActQueue' iv_abap_fieldname = 'ACT_QUEUE' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_true ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Rsrc' iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_true ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'RsrcType' iv_abap_fieldname = 'RSRC_TYPE' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_true ).
lo_property->set_updatable( abap_true ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'RsrcGrp' iv_abap_fieldname = 'RSRC_GRP' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_true ).
lo_property->set_updatable( abap_true ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'ExccodeOverall' iv_abap_fieldname = 'EXCCODE_OVERALL' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).

lo_entity_type->bind_structure( iv_structure_name   = '/SCWM/RSRC'
                                iv_bind_conversions = 'X' ). "#EC NOTEXT


***********************************************************************************************************************************
*   ENTITY SETS
***********************************************************************************************************************************
lo_entity_set = lo_entity_type->create_entity_set( 'RobotSet' ). "#EC NOTEXT

lo_entity_set->set_creatable( abap_true ).
lo_entity_set->set_updatable( abap_true ).
lo_entity_set->set_deletable( abap_false ).

lo_entity_set->set_pageable( abap_false ).
lo_entity_set->set_addressable( abap_true ).
lo_entity_set->set_has_ftxt_search( abap_false ).
lo_entity_set->set_subscribable( abap_false ).
lo_entity_set->set_filter_required( abap_false ).
  endmethod.


  method DEFINE_STORAGEBIN.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


  data:
        lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,                "#EC NEEDED
        lo_entity_type    type ref to /iwbep/if_mgw_odata_entity_typ,                "#EC NEEDED
        lo_complex_type   type ref to /iwbep/if_mgw_odata_cmplx_type,                "#EC NEEDED
        lo_property       type ref to /iwbep/if_mgw_odata_property,                  "#EC NEEDED
        lo_entity_set     type ref to /iwbep/if_mgw_odata_entity_set.                "#EC NEEDED

***********************************************************************************************************************************
*   ENTITY - StorageBin
***********************************************************************************************************************************

lo_entity_type = model->create_entity_type( iv_entity_type_name = 'StorageBin' iv_def_entity_set = abap_false ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************

lo_property = lo_entity_type->create_property( iv_property_name = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lgpla' iv_abap_fieldname = 'LGPLA' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lgtyp' iv_abap_fieldname = 'LGTYP' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lgber' iv_abap_fieldname = 'LGBER' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lptyp' iv_abap_fieldname = 'LPTYP' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Aisle' iv_abap_fieldname = 'AISLE' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Stack' iv_abap_fieldname = 'STACK' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'LvlV' iv_abap_fieldname = 'LVL_V' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'XCord' iv_abap_fieldname = 'X_CORD' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_precison( iv_precision = 3 ). "#EC NOTEXT
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'YCord' iv_abap_fieldname = 'Y_CORD' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_precison( iv_precision = 3 ). "#EC NOTEXT
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'ZCord' iv_abap_fieldname = 'Z_CORD' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_precison( iv_precision = 3 ). "#EC NOTEXT
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).

lo_entity_type->bind_structure( iv_structure_name   = '/SCWM/LAGP'
                                iv_bind_conversions = 'X' ). "#EC NOTEXT


***********************************************************************************************************************************
*   ENTITY SETS
***********************************************************************************************************************************
lo_entity_set = lo_entity_type->create_entity_set( 'StorageBinSet' ). "#EC NOTEXT

lo_entity_set->set_creatable( abap_false ).
lo_entity_set->set_updatable( abap_true ).
lo_entity_set->set_deletable( abap_false ).

lo_entity_set->set_pageable( abap_false ).
lo_entity_set->set_addressable( abap_true ).
lo_entity_set->set_has_ftxt_search( abap_false ).
lo_entity_set->set_subscribable( abap_false ).
lo_entity_set->set_filter_required( abap_false ).
  endmethod.


  method DEFINE_WAREHOUSEDESCRIPTION.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


  data:
        lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,                "#EC NEEDED
        lo_entity_type    type ref to /iwbep/if_mgw_odata_entity_typ,                "#EC NEEDED
        lo_complex_type   type ref to /iwbep/if_mgw_odata_cmplx_type,                "#EC NEEDED
        lo_property       type ref to /iwbep/if_mgw_odata_property,                  "#EC NEEDED
        lo_entity_set     type ref to /iwbep/if_mgw_odata_entity_set.                "#EC NEEDED

***********************************************************************************************************************************
*   ENTITY - WarehouseDescription
***********************************************************************************************************************************

lo_entity_type = model->create_entity_type( iv_entity_type_name = 'WarehouseDescription' iv_def_entity_set = abap_false ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************

lo_property = lo_entity_type->create_property( iv_property_name = 'Spras' iv_abap_fieldname = 'SPRAS' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 2 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'ISOLA' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lnumt' iv_abap_fieldname = 'LNUMT' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 40 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).

lo_entity_type->bind_structure( iv_structure_name   = '/SCWM/T300T'
                                iv_bind_conversions = 'X' ). "#EC NOTEXT


***********************************************************************************************************************************
*   ENTITY SETS
***********************************************************************************************************************************
lo_entity_set = lo_entity_type->create_entity_set( 'WarehouseDescriptionSet' ). "#EC NOTEXT

lo_entity_set->set_creatable( abap_false ).
lo_entity_set->set_updatable( abap_false ).
lo_entity_set->set_deletable( abap_false ).

lo_entity_set->set_pageable( abap_false ).
lo_entity_set->set_addressable( abap_true ).
lo_entity_set->set_has_ftxt_search( abap_false ).
lo_entity_set->set_subscribable( abap_false ).
lo_entity_set->set_filter_required( abap_false ).
  endmethod.


  method DEFINE_WAREHOUSENUMBER.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


  data:
        lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,                "#EC NEEDED
        lo_entity_type    type ref to /iwbep/if_mgw_odata_entity_typ,                "#EC NEEDED
        lo_complex_type   type ref to /iwbep/if_mgw_odata_cmplx_type,                "#EC NEEDED
        lo_property       type ref to /iwbep/if_mgw_odata_property,                  "#EC NEEDED
        lo_entity_set     type ref to /iwbep/if_mgw_odata_entity_set.                "#EC NEEDED

***********************************************************************************************************************************
*   ENTITY - WarehouseNumber
***********************************************************************************************************************************

lo_entity_type = model->create_entity_type( iv_entity_type_name = 'WarehouseNumber' iv_def_entity_set = abap_false ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************

lo_property = lo_entity_type->create_property( iv_property_name = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).

lo_entity_type->bind_structure( iv_structure_name   = '/SCWM/T300'
                                iv_bind_conversions = 'X' ). "#EC NOTEXT


***********************************************************************************************************************************
*   ENTITY SETS
***********************************************************************************************************************************
lo_entity_set = lo_entity_type->create_entity_set( 'WarehouseNumberSet' ). "#EC NOTEXT

lo_entity_set->set_creatable( abap_false ).
lo_entity_set->set_updatable( abap_false ).
lo_entity_set->set_deletable( abap_false ).

lo_entity_set->set_pageable( abap_false ).
lo_entity_set->set_addressable( abap_true ).
lo_entity_set->set_has_ftxt_search( abap_false ).
lo_entity_set->set_subscribable( abap_false ).
lo_entity_set->set_filter_required( abap_false ).
  endmethod.


  method DEFINE_WAREHOUSEORDER.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


  data:
        lo_annotation     type ref to /iwbep/if_mgw_odata_annotation,                "#EC NEEDED
        lo_entity_type    type ref to /iwbep/if_mgw_odata_entity_typ,                "#EC NEEDED
        lo_complex_type   type ref to /iwbep/if_mgw_odata_cmplx_type,                "#EC NEEDED
        lo_property       type ref to /iwbep/if_mgw_odata_property,                  "#EC NEEDED
        lo_entity_set     type ref to /iwbep/if_mgw_odata_entity_set.                "#EC NEEDED

***********************************************************************************************************************************
*   ENTITY - WarehouseOrder
***********************************************************************************************************************************

lo_entity_type = model->create_entity_type( iv_entity_type_name = 'WarehouseOrder' iv_def_entity_set = abap_false ). "#EC NOTEXT

***********************************************************************************************************************************
*Properties
***********************************************************************************************************************************

lo_property = lo_entity_type->create_property( iv_property_name = 'Lgnum' iv_abap_fieldname = 'LGNUM' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_true ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Who' iv_abap_fieldname = 'WHO' ). "#EC NOTEXT
lo_property->set_is_key( ).
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Status' iv_abap_fieldname = 'STATUS' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 1 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Areawho' iv_abap_fieldname = 'AREAWHO' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lgtyp' iv_abap_fieldname = 'LGTYP' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lgpla' iv_abap_fieldname = 'LGPLA' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Queue' iv_abap_fieldname = 'QUEUE' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Rsrc' iv_abap_fieldname = 'RSRC' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 18 ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Lsd' iv_abap_fieldname = 'LSD' ). "#EC NOTEXT
lo_property->set_type_edm_decimal( ).
lo_property->set_maxlength( iv_max_length = 15 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'TSTWH' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Topwhoid' iv_abap_fieldname = 'TOPWHOID' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_true ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Refwhoid' iv_abap_fieldname = 'REFWHOID' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 10 ). "#EC NOTEXT
lo_property->set_conversion_exit( 'ALPH0' ). "#EC NOTEXT
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Flgwho' iv_abap_fieldname = 'FLGWHO' ). "#EC NOTEXT
lo_property->set_type_edm_boolean( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).
lo_property = lo_entity_type->create_property( iv_property_name = 'Flgto' iv_abap_fieldname = 'FLGTO' ). "#EC NOTEXT
lo_property->set_type_edm_boolean( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).
lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_false ).
lo_property->set_filterable( abap_false ).
lo_property->/iwbep/if_mgw_odata_annotatabl~create_annotation( 'sap' )->add(
      EXPORTING
        iv_key      = 'unicode'
        iv_value    = 'false' ).

lo_entity_type->bind_structure( iv_structure_name   = '/SCWM/WHO'
                                iv_bind_conversions = 'X' ). "#EC NOTEXT


***********************************************************************************************************************************
*   ENTITY SETS
***********************************************************************************************************************************
lo_entity_set = lo_entity_type->create_entity_set( 'WarehouseOrderSet' ). "#EC NOTEXT

lo_entity_set->set_creatable( abap_false ).
lo_entity_set->set_updatable( abap_false ).
lo_entity_set->set_deletable( abap_false ).

lo_entity_set->set_pageable( abap_false ).
lo_entity_set->set_addressable( abap_true ).
lo_entity_set->set_has_ftxt_search( abap_false ).
lo_entity_set->set_subscribable( abap_false ).
lo_entity_set->set_filter_required( abap_false ).
  endmethod.


  method GET_LAST_MODIFIED.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


  CONSTANTS: lc_gen_date_time TYPE timestamp VALUE '20190416085233'.                  "#EC NOTEXT
  rv_last_modified = super->get_last_modified( ).
  IF rv_last_modified LT lc_gen_date_time.
    rv_last_modified = lc_gen_date_time.
  ENDIF.
  endmethod.


  method LOAD_TEXT_ELEMENTS.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS         &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL  &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                   &*
*&                                                                     &*
*&---------------------------------------------------------------------*


DATA:
     ls_text_element TYPE ts_text_element.                                 "#EC NEEDED
CLEAR ls_text_element.


clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetNewRobotWarehouseOrder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '021'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetNewRobotWarehouseOrder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '020'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Exccode'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SetRobotStatus'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '008'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SetRobotStatus'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '009'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SetRobotStatus'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '010'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetRobotWarehouseOrders'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '027'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetRobotWarehouseOrders'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '026'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTaskFirstStep'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '030'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTaskFirstStep'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '029'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Tanum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTaskFirstStep'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '028'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'NoWho'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetNewRobotTypeWarehouseOrders'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '024'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetNewRobotTypeWarehouseOrders'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '022'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'RsrcGrp'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetNewRobotTypeWarehouseOrders'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '031'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'RsrcType'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'GetNewRobotTypeWarehouseOrders'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '025'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Who'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'UnassignRobotFromWarehouseorder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '036'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'UnassignRobotFromWarehouseorder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '035'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'UnassignRobotFromWarehouseorder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '034'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Tanum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendFirstConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '046'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Who'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendFirstConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '042'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendFirstConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '041'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendFirstConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '040'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '013'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Tanum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '012'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Nista'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '011'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Altme'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '016'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Nlenr'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '015'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Parti'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '014'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Nlpla'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '032'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'ConfExc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'ConfirmWarehouseTask'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '033'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'AssignRobotToWarehouseOrder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '019'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'AssignRobotToWarehouseOrder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '018'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Who'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'AssignRobotToWarehouseOrder'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '017'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.

clear ls_text_element.
ls_text_element-artifact_name          = 'Lgnum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendSecondConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '043'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Rsrc'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendSecondConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '044'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Who'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendSecondConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '045'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
clear ls_text_element.
ls_text_element-artifact_name          = 'Tanum'.                               "#EC NOTEXT
ls_text_element-artifact_type          = 'FIPA'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_type   = 'FIMP'.                                                "#EC NOTEXT
ls_text_element-parent_artifact_name   = 'SendSecondConfirmationError'.                                      "#EC NOTEXT
ls_text_element-text_symbol            = '047'.                            "#EC NOTEXT
APPEND ls_text_element TO rt_text_elements.
  endmethod.
ENDCLASS.
