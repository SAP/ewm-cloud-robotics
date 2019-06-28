*---------------------------------------------------------------------*
*    program for:   TABLEFRAME_ZEWM_TRSRC_TYP
*   generation date: 25.04.2019 at 10:53:30
*   view maintenance generator version: #001407#
*---------------------------------------------------------------------*
FUNCTION TABLEFRAME_ZEWM_TRSRC_TYP     .

  PERFORM TABLEFRAME TABLES X_HEADER X_NAMTAB DBA_SELLIST DPL_SELLIST
                            EXCL_CUA_FUNCT
                     USING  CORR_NUMBER VIEW_ACTION VIEW_NAME.

ENDFUNCTION.
