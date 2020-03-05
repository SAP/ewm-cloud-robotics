*---------------------------------------------------------------------*
*    view related data declarations
*   generation date: 05.03.2020 at 10:43:18
*   view maintenance generator version: #001407#
*---------------------------------------------------------------------*
*...processing: ZEWM_V_ERR_QUEUE................................*
TABLES: ZEWM_V_ERR_QUEUE, *ZEWM_V_ERR_QUEUE. "view work areas
CONTROLS: TCTRL_ZEWM_V_ERR_QUEUE
TYPE TABLEVIEW USING SCREEN '0001'.
DATA: BEGIN OF STATUS_ZEWM_V_ERR_QUEUE. "state vector
          INCLUDE STRUCTURE VIMSTATUS.
DATA: END OF STATUS_ZEWM_V_ERR_QUEUE.
* Table for entries selected to show on screen
DATA: BEGIN OF ZEWM_V_ERR_QUEUE_EXTRACT OCCURS 0010.
INCLUDE STRUCTURE ZEWM_V_ERR_QUEUE.
          INCLUDE STRUCTURE VIMFLAGTAB.
DATA: END OF ZEWM_V_ERR_QUEUE_EXTRACT.
* Table for all entries loaded from database
DATA: BEGIN OF ZEWM_V_ERR_QUEUE_TOTAL OCCURS 0010.
INCLUDE STRUCTURE ZEWM_V_ERR_QUEUE.
          INCLUDE STRUCTURE VIMFLAGTAB.
DATA: END OF ZEWM_V_ERR_QUEUE_TOTAL.

*.........table declarations:.................................*
TABLES: /SCWM/TRSRC_GRP                .
