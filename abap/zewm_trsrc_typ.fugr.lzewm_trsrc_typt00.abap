*---------------------------------------------------------------------*
*    view related data declarations
*   generation date: 25.04.2019 at 10:53:31
*   view maintenance generator version: #001407#
*---------------------------------------------------------------------*
*...processing: ZEWM_TRSRC_TYP..................................*
DATA:  BEGIN OF STATUS_ZEWM_TRSRC_TYP                .   "state vector
         INCLUDE STRUCTURE VIMSTATUS.
DATA:  END OF STATUS_ZEWM_TRSRC_TYP                .
CONTROLS: TCTRL_ZEWM_TRSRC_TYP
            TYPE TABLEVIEW USING SCREEN '0001'.
*.........table declarations:.................................*
TABLES: *ZEWM_TRSRC_TYP                .
TABLES: ZEWM_TRSRC_TYP                 .

* general table data declarations..............
  INCLUDE LSVIMTDT                                .
